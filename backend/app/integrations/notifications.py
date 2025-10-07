"""
알림 발송 통합 모듈 (Slack, Discord)
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """알림 타입"""
    SLACK = "slack"
    DISCORD = "discord"


class NotificationSender:
    """알림 발송 기본 클래스"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def send(self, message: str, **kwargs) -> bool:
        """
        알림 발송

        Args:
            message: 발송할 메시지
            **kwargs: 추가 옵션

        Returns:
            성공 여부
        """
        raise NotImplementedError("Subclass must implement send()")


class SlackNotifier(NotificationSender):
    """
    Slack Webhook 알림 발송

    Usage:
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/...")
        notifier.send_markdown("# Hello\nWorld")
        notifier.send_blocks([...])  # Slack Block Kit
    """

    def __init__(self, webhook_url: Optional[str] = None):
        super().__init__(webhook_url or os.getenv('SLACK_WEBHOOK_URL'))
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL이 설정되지 않았습니다.")

    def send(self, message: str, username: str = "부동산 봇", emoji: str = ":house:") -> bool:
        """
        일반 텍스트 메시지 발송

        Args:
            message: 메시지 내용
            username: 표시될 봇 이름
            emoji: 아이콘 이모지

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            logger.error("Slack Webhook URL이 설정되지 않았습니다.")
            return False

        payload = {
            "text": message,
            "username": username,
            "icon_emoji": emoji
        }

        try:
            response = self.session.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Slack 메시지 전송 성공")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack 메시지 전송 실패: {e}")
            return False

    def send_markdown(
        self,
        markdown_text: str,
        username: str = "부동산 봇",
        emoji: str = ":house:"
    ) -> bool:
        """
        마크다운 형식 메시지 발송 (Slack mrkdwn)

        Args:
            markdown_text: 마크다운 텍스트
            username: 표시될 봇 이름
            emoji: 아이콘 이모지

        Returns:
            성공 여부
        """
        # Slack은 일부 마크다운만 지원하므로 변환
        slack_text = self._convert_markdown_to_slack(markdown_text)
        return self.send(slack_text, username=username, emoji=emoji)

    def send_blocks(
        self,
        blocks: list,
        text: str = "",
        username: str = "부동산 봇",
        emoji: str = ":house:"
    ) -> bool:
        """
        Slack Block Kit 사용하여 발송

        Args:
            blocks: Slack Block Kit 블록 리스트
            text: 폴백 텍스트
            username: 표시될 봇 이름
            emoji: 아이콘 이모지

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            logger.error("Slack Webhook URL이 설정되지 않았습니다.")
            return False

        payload = {
            "blocks": blocks,
            "text": text or "새로운 알림이 있습니다.",
            "username": username,
            "icon_emoji": emoji
        }

        try:
            response = self.session.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Slack 블록 메시지 전송 성공")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack 블록 메시지 전송 실패: {e}")
            return False

    @staticmethod
    def _convert_markdown_to_slack(markdown: str) -> str:
        """
        마크다운을 Slack mrkdwn 형식으로 변환

        Slack mrkdwn 지원:
        - *bold* (볼드)
        - _italic_ (이탤릭)
        - ~strike~ (취소선)
        - `code` (코드)
        - ```code block``` (코드 블록)
        - > quote (인용)
        """
        # 기본적으로 대부분 호환되지만 일부 변환 필요
        text = markdown

        # 헤더를 볼드로 변환 (Slack은 헤더를 지원하지 않음)
        text = text.replace('### ', '*')
        text = text.replace('## ', '*')
        text = text.replace('# ', '*')

        # 링크 형식 변환: [text](url) -> <url|text>
        import re
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<\2|\1>', text)

        return text


class DiscordNotifier(NotificationSender):
    """
    Discord Webhook 알림 발송

    Usage:
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/...")
        notifier.send_markdown("# Hello\nWorld")
        notifier.send_embed({...})  # Discord Embed
    """

    def __init__(self, webhook_url: Optional[str] = None):
        super().__init__(webhook_url or os.getenv('DISCORD_WEBHOOK_URL'))
        if not self.webhook_url:
            logger.warning("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")

    def send(self, message: str, username: str = "부동산 봇") -> bool:
        """
        일반 텍스트 메시지 발송

        Args:
            message: 메시지 내용
            username: 표시될 봇 이름

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            logger.error("Discord Webhook URL이 설정되지 않았습니다.")
            return False

        payload = {
            "content": message,
            "username": username
        }

        try:
            response = self.session.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Discord 메시지 전송 성공")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Discord 메시지 전송 실패: {e}")
            return False

    def send_markdown(self, markdown_text: str, username: str = "부동산 봇") -> bool:
        """
        마크다운 형식 메시지 발송

        Discord는 마크다운을 잘 지원하므로 그대로 전송

        Args:
            markdown_text: 마크다운 텍스트
            username: 표시될 봇 이름

        Returns:
            성공 여부
        """
        return self.send(markdown_text, username=username)

    def send_embed(
        self,
        title: str,
        description: str,
        fields: Optional[list] = None,
        color: int = 0x00ff00,  # 기본: 초록색
        footer: Optional[str] = None,
        username: str = "부동산 봇"
    ) -> bool:
        """
        Discord Embed 형식으로 발송

        Args:
            title: 제목
            description: 설명
            fields: 필드 리스트 [{"name": "...", "value": "...", "inline": True}, ...]
            color: 색상 (16진수)
            footer: 푸터 텍스트
            username: 표시될 봇 이름

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            logger.error("Discord Webhook URL이 설정되지 않았습니다.")
            return False

        embed = {
            "title": title,
            "description": description,
            "color": color
        }

        if fields:
            embed["fields"] = fields

        if footer:
            embed["footer"] = {"text": footer}

        payload = {
            "username": username,
            "embeds": [embed]
        }

        try:
            response = self.session.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Discord Embed 전송 성공")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Discord Embed 전송 실패: {e}")
            return False


class NotificationManager:
    """
    통합 알림 관리자

    Usage:
        manager = NotificationManager()
        manager.send_to_all("Hello World!")
        manager.send_markdown_to_all("# Title\nContent")
    """

    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        discord_webhook: Optional[str] = None
    ):
        self.slack = SlackNotifier(slack_webhook)
        self.discord = DiscordNotifier(discord_webhook)

    def send_to_all(self, message: str) -> Dict[str, bool]:
        """
        모든 채널에 메시지 발송

        Args:
            message: 발송할 메시지

        Returns:
            각 채널별 성공 여부 딕셔너리
        """
        results = {}

        if self.slack.webhook_url:
            results['slack'] = self.slack.send(message)

        if self.discord.webhook_url:
            results['discord'] = self.discord.send(message)

        return results

    def send_markdown_to_all(self, markdown_text: str) -> Dict[str, bool]:
        """
        모든 채널에 마크다운 메시지 발송

        Args:
            markdown_text: 마크다운 텍스트

        Returns:
            각 채널별 성공 여부 딕셔너리
        """
        results = {}

        if self.slack.webhook_url:
            results['slack'] = self.slack.send_markdown(markdown_text)

        if self.discord.webhook_url:
            results['discord'] = self.discord.send_markdown(markdown_text)

        return results

    def is_configured(self) -> bool:
        """최소 하나 이상의 채널이 설정되어 있는지 확인"""
        return bool(self.slack.webhook_url or self.discord.webhook_url)


# 편의 함수들
def send_to_slack(message: str, markdown: bool = False) -> bool:
    """Slack으로 메시지 전송"""
    notifier = SlackNotifier()
    if markdown:
        return notifier.send_markdown(message)
    return notifier.send(message)


def send_to_discord(message: str, markdown: bool = False) -> bool:
    """Discord로 메시지 전송"""
    notifier = DiscordNotifier()
    if markdown:
        return notifier.send_markdown(message)
    return notifier.send(message)


def send_to_all(message: str, markdown: bool = False) -> Dict[str, bool]:
    """모든 채널에 메시지 전송"""
    manager = NotificationManager()
    if markdown:
        return manager.send_markdown_to_all(message)
    return manager.send_to_all(message)
