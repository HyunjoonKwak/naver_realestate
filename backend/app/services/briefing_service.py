"""
주간 브리핑 생성 및 발송 서비스
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.complex import Complex, ArticleChange
from app.services.article_tracker import ArticleTracker
from app.integrations.notifications import NotificationManager

logger = logging.getLogger(__name__)


class BriefingService:
    """주간 브리핑 생성 및 발송 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.tracker = ArticleTracker(db)
        # 환경변수에서 Webhook URL 읽기
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        self.notification_manager = NotificationManager(
            slack_webhook=slack_webhook,
            discord_webhook=discord_webhook
        )

    def generate_weekly_briefing(
        self,
        days: int = 7,
        mark_as_read: bool = True
    ) -> Dict:
        """
        주간 브리핑 생성

        Args:
            days: 조회할 일수 (기본: 7일)
            mark_as_read: 생성 후 변동사항을 읽음으로 표시할지 여부

        Returns:
            브리핑 데이터 딕셔너리
        """
        logger.info(f"📊 주간 브리핑 생성 시작 (지난 {days}일)")

        since = datetime.now() - timedelta(days=days)
        end_date = datetime.now()

        # 모든 등록된 단지 조회
        complexes = self.db.query(Complex).all()

        if not complexes:
            logger.warning("등록된 단지가 없습니다.")
            return {
                'period': {'start': since, 'end': end_date, 'days': days},
                'complexes': [],
                'total_summary': self._get_empty_summary(),
                'markdown': self._generate_empty_briefing_markdown(since, end_date)
            }

        # 전체 변동사항 조회
        all_changes = (
            self.db.query(ArticleChange)
            .filter(
                ArticleChange.detected_at >= since,
                ArticleChange.is_read == False  # 읽지 않은 변동사항만
            )
            .all()
        )

        # 단지별 변동사항 집계
        complex_data = []
        total_summary = {
            'new': 0,
            'removed': 0,
            'price_up': 0,
            'price_down': 0,
            'total': 0
        }

        for complex_obj in complexes:
            complex_id = complex_obj.complex_id

            # 해당 단지의 변동사항 필터링
            complex_changes = [c for c in all_changes if c.complex_id == complex_id]

            if not complex_changes:
                continue  # 변동사항이 없는 단지는 건너뛰기

            # 변동사항 분류
            new_count = len([c for c in complex_changes if c.change_type == 'NEW'])
            removed_count = len([c for c in complex_changes if c.change_type == 'REMOVED'])
            price_up_count = len([c for c in complex_changes if c.change_type == 'PRICE_UP'])
            price_down_count = len([c for c in complex_changes if c.change_type == 'PRICE_DOWN'])

            # 가장 큰 가격 변동 찾기
            price_changes = [c for c in complex_changes if c.change_type in ['PRICE_UP', 'PRICE_DOWN']]
            most_significant_change = None
            if price_changes:
                most_significant_change = max(
                    price_changes,
                    key=lambda c: abs(c.price_change_percent) if c.price_change_percent else 0
                )

            summary = {
                'new': new_count,
                'removed': removed_count,
                'price_up': price_up_count,
                'price_down': price_down_count,
                'total': len(complex_changes),
                'most_significant_change': most_significant_change
            }

            complex_data.append({
                'complex': complex_obj,
                'summary': summary,
                'changes': complex_changes
            })

            # 전체 요약에 합산
            total_summary['new'] += new_count
            total_summary['removed'] += removed_count
            total_summary['price_up'] += price_up_count
            total_summary['price_down'] += price_down_count
            total_summary['total'] += len(complex_changes)

        # 마크다운 생성
        markdown = self._generate_briefing_markdown(
            since,
            end_date,
            complex_data,
            total_summary
        )

        # 읽음 처리
        if mark_as_read and all_changes:
            for change in all_changes:
                change.is_read = True
            self.db.commit()
            logger.info(f"✅ {len(all_changes)}건의 변동사항을 읽음으로 표시")

        briefing_data = {
            'period': {
                'start': since,
                'end': end_date,
                'days': days
            },
            'complexes': complex_data,
            'total_summary': total_summary,
            'markdown': markdown
        }

        logger.info(f"✅ 주간 브리핑 생성 완료 (총 {len(complex_data)}개 단지, {total_summary['total']}건 변동)")
        return briefing_data

    def send_briefing(
        self,
        days: int = 7,
        to_slack: bool = True,
        to_discord: bool = True,
        crawl_stats: Dict = None
    ) -> Dict:
        """
        주간 브리핑 생성 및 발송

        Args:
            days: 조회할 일수
            to_slack: Slack 전송 여부
            to_discord: Discord 전송 여부
            crawl_stats: 크롤링 통계 (선택사항)

        Returns:
            발송 결과 딕셔너리
        """
        # 브리핑 생성
        briefing = self.generate_weekly_briefing(days=days, mark_as_read=True)

        # 크롤링 통계 추가
        if crawl_stats:
            briefing['crawl_stats'] = crawl_stats

        # 알림 채널이 설정되지 않은 경우
        if not self.notification_manager.is_configured():
            logger.error("❌ 알림 채널이 설정되지 않았습니다. 환경변수를 확인하세요.")
            return {
                'success': False,
                'error': 'No notification channels configured',
                'briefing': briefing
            }

        # 변동사항이 없는 경우
        if briefing['total_summary']['total'] == 0:
            # 크롤링 통계가 있으면 "변동사항 없음" 메시지로 브리핑 전송
            if not crawl_stats:
                logger.info("ℹ️  변동사항이 없어 알림을 전송하지 않습니다.")
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'No changes to report',
                    'briefing': briefing
                }
            # 크롤링 통계가 있으면 계속 진행하여 "변동사항 없음" 브리핑 전송
            logger.info("ℹ️  변동사항은 없지만 크롤링 통계 브리핑을 전송합니다.")

        # 알림 발송
        markdown = briefing['markdown']

        # 크롤링 통계가 있으면 마크다운에 추가
        if crawl_stats:
            crawl_summary = self._generate_crawl_summary_markdown(crawl_stats)
            markdown = crawl_summary + "\n\n" + markdown

        results = {}

        if to_slack and self.notification_manager.slack.webhook_url:
            logger.info("📤 Slack으로 브리핑 전송 중...")
            results['slack'] = self.notification_manager.slack.send_markdown(markdown)

        if to_discord and self.notification_manager.discord.webhook_url:
            logger.info("📤 Discord로 브리핑 전송 중...")
            results['discord'] = self.notification_manager.discord.send_markdown(markdown)

        success = any(results.values())

        if success:
            logger.info(f"✅ 브리핑 전송 완료: {results}")
        else:
            logger.error(f"❌ 브리핑 전송 실패: {results}")

        return {
            'success': success,
            'results': results,
            'briefing': briefing
        }

    def _generate_briefing_markdown(
        self,
        start_date: datetime,
        end_date: datetime,
        complex_data: List[Dict],
        total_summary: Dict
    ) -> str:
        """
        브리핑 마크다운 생성

        Args:
            start_date: 시작일
            end_date: 종료일
            complex_data: 단지별 데이터
            total_summary: 전체 요약

        Returns:
            마크다운 문자열
        """
        lines = []

        # 헤더
        lines.append("# 🏠 주간 부동산 브리핑")
        lines.append("")
        lines.append(f"📅 **기간**: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        lines.append("")

        # 전체 요약
        lines.append("## 📊 전체 요약")
        lines.append(f"- 총 단지 수: **{len(complex_data)}개**")
        lines.append(f"- 신규 매물: **{total_summary['new']}건** 🆕")
        lines.append(f"- 삭제 매물: **{total_summary['removed']}건** ❌")
        lines.append(f"- 가격 변동: **{total_summary['price_up'] + total_summary['price_down']}건** (↑{total_summary['price_up']}건, ↓{total_summary['price_down']}건)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 단지별 상세
        lines.append("## 🏢 단지별 상세 정보")
        lines.append("")

        for data in complex_data:
            complex_obj = data['complex']
            summary = data['summary']
            most_sig = summary.get('most_significant_change')

            lines.append(f"### {complex_obj.complex_name}")
            lines.append(f"- **신규 매물**: {summary['new']}건")
            lines.append(f"- **삭제 매물**: {summary['removed']}건")
            lines.append(f"- **가격 상승**: {summary['price_up']}건")
            lines.append(f"- **가격 하락**: {summary['price_down']}건")

            # 가장 큰 변동 하이라이트
            if most_sig:
                change_icon = "📈" if most_sig.change_type == 'PRICE_UP' else "📉"
                lines.append(f"- {change_icon} **주목**: {most_sig.area_name or ''} {most_sig.trade_type or ''} "
                           f"{most_sig.old_price} → {most_sig.new_price} "
                           f"({most_sig.price_change_percent:+.1f}%)")

            lines.append("")

        # 푸터
        lines.append("---")
        lines.append("")
        next_briefing = end_date + timedelta(days=7)
        lines.append(f"⏰ **다음 브리핑**: {next_briefing.strftime('%Y-%m-%d (%a)')}")
        lines.append("")
        lines.append("_이 브리핑은 자동으로 생성되었습니다._")

        return "\n".join(lines)

    def _generate_empty_briefing_markdown(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """변동사항이 없을 때의 브리핑"""
        lines = []
        lines.append("# 🏠 주간 부동산 브리핑")
        lines.append("")
        lines.append(f"📅 **기간**: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("## ✅ 변동사항 없음")
        lines.append("")
        lines.append("✨ 지난 주간 모니터링 대상 단지의 매물 가격 및 매물 수에 변동이 없습니다.")
        lines.append("")
        lines.append("- 신규 매물: 없음")
        lines.append("- 삭제된 매물: 없음")
        lines.append("- 가격 변동: 없음")
        lines.append("")
        lines.append("💡 시장이 안정적인 상태를 유지하고 있습니다.")
        lines.append("")
        lines.append("---")
        lines.append("")
        next_briefing = end_date + timedelta(days=7)
        lines.append(f"⏰ **다음 브리핑**: {next_briefing.strftime('%Y-%m-%d (%a)')}")

        return "\n".join(lines)

    @staticmethod
    def _get_empty_summary() -> Dict:
        """빈 요약 데이터"""
        return {
            'new': 0,
            'removed': 0,
            'price_up': 0,
            'price_down': 0,
            'total': 0
        }

    @staticmethod
    def _generate_crawl_summary_markdown(crawl_stats: Dict) -> str:
        """
        크롤링 통계 요약 마크다운 생성

        Args:
            crawl_stats: 크롤링 통계 딕셔너리

        Returns:
            마크다운 문자열
        """
        lines = []
        lines.append("# 🤖 자동 크롤링 완료")
        lines.append("")

        # 시작/종료 시간
        started_at = crawl_stats.get('started_at', '')
        finished_at = crawl_stats.get('finished_at', '')
        if started_at and finished_at:
            from datetime import datetime
            start_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            finish_dt = datetime.fromisoformat(finished_at.replace('Z', '+00:00'))
            lines.append(f"⏰ **시작**: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"⏰ **완료**: {finish_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            duration = crawl_stats.get('duration_seconds', 0)
            lines.append(f"⏱️ **소요시간**: {duration}초 ({duration // 60}분 {duration % 60}초)")
            lines.append("")

        # 크롤링 결과
        lines.append("## 📊 크롤링 결과")
        lines.append(f"- 대상 단지: **{crawl_stats.get('total_complexes', 0)}개**")
        lines.append(f"- 성공: **{crawl_stats.get('success', 0)}개** ✅")
        lines.append(f"- 실패: **{crawl_stats.get('failed', 0)}개** ❌")
        lines.append(f"- 수집 매물: **{crawl_stats.get('total_articles_collected', 0)}건**")
        lines.append(f"- 신규 매물: **{crawl_stats.get('total_articles_new', 0)}건** 🆕")

        # 에러가 있으면 표시
        errors = crawl_stats.get('errors', [])
        if errors:
            lines.append("")
            lines.append("### ⚠️ 오류 발생")
            for error in errors[:3]:  # 최대 3개만 표시
                lines.append(f"- {error}")

        lines.append("")
        lines.append("---")

        return "\n".join(lines)
