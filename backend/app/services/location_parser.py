"""
법정동 코드 파싱 및 주소 매칭 서비스
"""
import os
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class LocationParser:
    """법정동 코드 파싱 및 주소 매칭"""

    def __init__(self):
        self.dong_code_map: Dict[str, str] = {}
        self.sigungu_code_map: Dict[str, str] = {}
        self._load_dong_codes()

    def _load_dong_codes(self):
        """법정동 코드 파일 로드"""
        # 파일 경로
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(current_dir, "..", "data", "dong_code_active.txt")

        if not os.path.exists(data_file):
            logger.warning(f"법정동 코드 파일을 찾을 수 없습니다: {data_file}")
            return

        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                # 첫 줄 헤더 건너뛰기
                next(f)

                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split('\t')
                    if len(parts) != 2:
                        continue

                    code = parts[0].strip()
                    name = parts[1].strip()

                    # 전체 주소 → 법정동 코드 매핑
                    self.dong_code_map[name] = code

                    # 시군구 코드 추출 (앞 5자리)
                    sigungu_code = code[:5]

                    # 시군구 이름 추출 (예: "경기도 성남시 분당구")
                    # 동 단위가 아닌 경우 (코드가 00으로 끝나는 경우)
                    if code.endswith("00000"):
                        # 시군구 레벨
                        self.sigungu_code_map[name] = sigungu_code

            logger.info(f"법정동 코드 로드 완료: {len(self.dong_code_map)}개 주소, {len(self.sigungu_code_map)}개 시군구")

        except Exception as e:
            logger.error(f"법정동 코드 파일 로드 실패: {e}")

    def extract_sigungu_code(self, address: str) -> Optional[str]:
        """
        주소에서 시군구 코드 추출

        Args:
            address: 주소 문자열 (예: "경기도 성남시 분당구 정자동")

        Returns:
            시군구 코드 (5자리) 또는 None
        """
        if not address:
            return None

        # 정확한 매칭 시도
        for location_name, sigungu_code in self.sigungu_code_map.items():
            if location_name in address:
                return sigungu_code

        # 부분 매칭 시도 (동 포함)
        for location_name, full_code in self.dong_code_map.items():
            if location_name in address:
                return full_code[:5]

        # 수동 매핑 (하드코딩된 주요 지역)
        manual_map = {
            "강남구": "11680",
            "서초구": "11650",
            "송파구": "11710",
            "분당구": "41135",
            "수지구": "41465",
        }

        for key, code in manual_map.items():
            if key in address:
                return code

        logger.warning(f"시군구 코드를 찾을 수 없습니다: {address}")
        return None

    def get_location_info(self, address: str) -> Dict:
        """
        주소에서 위치 정보 추출

        Args:
            address: 주소 문자열

        Returns:
            위치 정보 딕셔너리 (시군구 코드, 이름 등)
        """
        sigungu_code = self.extract_sigungu_code(address)

        # 매칭된 위치 이름 찾기
        matched_location = None
        for location_name, code in self.sigungu_code_map.items():
            if code == sigungu_code:
                matched_location = location_name
                break

        return {
            "sigungu_code": sigungu_code,
            "location_name": matched_location,
            "original_address": address
        }

    def search_locations(self, query: str, limit: int = 10) -> List[Dict]:
        """
        위치 검색

        Args:
            query: 검색어
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        results = []

        for location_name, sigungu_code in self.sigungu_code_map.items():
            if query in location_name:
                results.append({
                    "name": location_name,
                    "code": sigungu_code
                })

                if len(results) >= limit:
                    break

        return results
