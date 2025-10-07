"""
국토교통부 실거래가 API 서비스
"""
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from .location_parser import LocationParser

logger = logging.getLogger(__name__)


class MOLITService:
    """국토교통부 아파트 실거래가 조회 서비스"""

    def __init__(self):
        # 환경변수에서 API 키 로드
        self.api_key = os.getenv("MOLIT_API_KEY", "")
        self.trade_api_url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev"
        self.rent_api_url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent"
        self.location_parser = LocationParser()

    def _parse_xml_response(self, xml_content: str) -> Dict:
        """
        XML 응답을 파싱하여 딕셔너리로 변환

        Args:
            xml_content: XML 문자열

        Returns:
            파싱된 데이터 딕셔너리
        """
        try:
            root = ET.fromstring(xml_content)
            items = []

            # header 정보
            header = root.find('header')
            result_code = header.find('resultCode').text if header is not None and header.find('resultCode') is not None else None
            result_msg = header.find('resultMsg').text if header is not None and header.find('resultMsg') is not None else None

            # body 정보
            body = root.find('body')
            if body is None:
                return {
                    'result_code': 'ERROR',
                    'result_msg': 'No body in response',
                    'total_count': 0,
                    'items': []
                }

            total_count = body.find('totalCount').text if body.find('totalCount') is not None else "0"

            # items 파싱
            items_element = body.find('items')
            if items_element is not None:
                for item in items_element.findall('item'):
                    item_data = {}
                    for child in item:
                        item_data[child.tag] = child.text if child.text else ""
                    items.append(item_data)

            return {
                'result_code': result_code,
                'result_msg': result_msg,
                'total_count': int(total_count),
                'items': items
            }
        except Exception as e:
            logger.error(f"XML 파싱 오류: {e}")
            return {
                'result_code': 'ERROR',
                'result_msg': f'XML 파싱 오류: {str(e)}',
                'total_count': 0,
                'items': []
            }

    def _fetch_all_pages(
        self,
        url: str,
        sigungu_code: str,
        year_month: str,
        complex_name: Optional[str] = None
    ) -> List[Dict]:
        """
        모든 페이지 데이터를 가져오는 메서드

        Args:
            url: API URL
            sigungu_code: 시군구 코드
            year_month: 조회 년월
            complex_name: 아파트 단지명 (필터용)

        Returns:
            모든 페이지의 아이템 리스트
        """
        all_items = []
        page_no = 1

        while True:
            params = {
                'serviceKey': self.api_key,
                'LAWD_CD': sigungu_code,
                'DEAL_YMD': year_month,
                'pageNo': page_no,
                'numOfRows': 1000
            }

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                # XML 파싱
                data = self._parse_xml_response(response.text)

                if data['result_code'] not in ['00', '000']:
                    if page_no == 1:
                        logger.warning(f"API 호출 실패: {data['result_code']} - {data.get('result_msg', '')}")
                    break

                # 단지명 필터링
                items = data['items']
                if complex_name:
                    items = [
                        item for item in items
                        if complex_name in item.get('아파트', '')
                    ]

                all_items.extend(items)

                # 모든 데이터를 가져왔는지 확인
                if len(data['items']) < 1000:
                    break

                page_no += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"API 호출 오류 (페이지 {page_no}): {e}")
                break

        return all_items

    def get_apt_trade_data(
        self,
        sigungu_code: str,
        year_month: str,
        complex_name: Optional[str] = None
    ) -> List[Dict]:
        """
        아파트 매매 실거래가 조회

        Args:
            sigungu_code: 시군구 코드 (예: 41135 - 성남시 분당구)
            year_month: 조회 년월 (예: 202501)
            complex_name: 아파트 단지명 (필터용, optional)

        Returns:
            실거래가 리스트
        """
        if not self.api_key:
            logger.warning("MOLIT_API_KEY가 설정되지 않았습니다.")
            return []

        url = f"{self.trade_api_url}/getRTMSDataSvcAptTradeDev"
        return self._fetch_all_pages(url, sigungu_code, year_month, complex_name)

    def get_apt_rent_data(
        self,
        sigungu_code: str,
        year_month: str,
        complex_name: Optional[str] = None
    ) -> List[Dict]:
        """
        아파트 전월세 실거래가 조회

        Args:
            sigungu_code: 시군구 코드
            year_month: 조회 년월
            complex_name: 아파트 단지명 (필터용)

        Returns:
            전월세 실거래가 리스트
        """
        if not self.api_key:
            logger.warning("MOLIT_API_KEY가 설정되지 않았습니다.")
            return []

        url = f"{self.rent_api_url}/getRTMSDataSvcAptRent"
        return self._fetch_all_pages(url, sigungu_code, year_month, complex_name)

    def get_recent_trades(
        self,
        sigungu_code: str,
        complex_name: str,
        months: int = 6,
        include_rent: bool = False
    ) -> List[Dict]:
        """
        최근 N개월 실거래가 조회

        Args:
            sigungu_code: 시군구 코드
            complex_name: 아파트 단지명
            months: 조회할 개월 수 (기본 6개월)
            include_rent: 전월세 포함 여부

        Returns:
            실거래가 리스트
        """
        all_trades = []

        # 현재 월부터 N개월 전까지 조회
        current_date = datetime.now()

        for i in range(months):
            target_date = current_date - timedelta(days=30 * i)
            year_month = target_date.strftime("%Y%m")

            # 매매 데이터 조회
            trades = self.get_apt_trade_data(
                sigungu_code=sigungu_code,
                year_month=year_month,
                complex_name=complex_name
            )
            all_trades.extend(trades)

            # 전월세 데이터 조회 (옵션)
            if include_rent:
                rent_trades = self.get_apt_rent_data(
                    sigungu_code=sigungu_code,
                    year_month=year_month,
                    complex_name=complex_name
                )
                all_trades.extend(rent_trades)

        return all_trades

    def parse_trade_to_dict(self, trade_item: Dict) -> Dict:
        """
        API 응답 아이템을 표준 딕셔너리로 변환

        Args:
            trade_item: API 응답 아이템

        Returns:
            표준화된 거래 정보
        """
        try:
            # 거래금액 파싱 (예: "12,500" -> 12500만원)
            deal_amount = trade_item.get("거래금액", "0").replace(",", "").strip()
            deal_amount_int = int(deal_amount) if deal_amount.isdigit() else 0

            # 거래일자 파싱 (예: "20250105" 형식으로 변환)
            year = trade_item.get("년", "")
            month = trade_item.get("월", "").zfill(2)
            day = trade_item.get("일", "").zfill(2)
            trade_date = f"{year}{month}{day}"

            # 전용면적
            exclusive_area_str = trade_item.get("전용면적", "0").strip()
            exclusive_area = float(exclusive_area_str) if exclusive_area_str else 0

            # 층
            floor_str = trade_item.get("층", "0").strip()
            floor = int(floor_str) if floor_str.isdigit() else 0

            return {
                "complex_name": trade_item.get("아파트", ""),
                "deal_price": deal_amount_int,  # 만원 단위
                "trade_date": trade_date,
                "exclusive_area": exclusive_area,
                "floor": floor,
                "sigungu": trade_item.get("시군구", ""),
                "dong": trade_item.get("법정동", ""),
                "jibun": trade_item.get("지번", ""),
            }
        except Exception as e:
            logger.error(f"거래 데이터 파싱 실패: {e}, 원본: {trade_item}")
            return {}

    def extract_sigungu_code(self, address: str) -> Optional[str]:
        """
        주소에서 시군구 코드 추출

        LocationParser를 사용하여 20,000개 이상의 법정동 코드에서 자동 추출

        Args:
            address: 주소 문자열

        Returns:
            시군구 코드 (5자리) 또는 None
        """
        return self.location_parser.extract_sigungu_code(address)
