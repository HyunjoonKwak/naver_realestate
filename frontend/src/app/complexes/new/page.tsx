'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function NewComplexPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [fetchingInfo, setFetchingInfo] = useState(false);
  const [error, setError] = useState('');
  const [naverUrl, setNaverUrl] = useState('');
  const [collectAddress, setCollectAddress] = useState(false);

  const [formData, setFormData] = useState({
    complex_id: '',
    complex_name: '',
    complex_type: '',
    total_households: '',
    total_dongs: '',
    completion_date: '',
    min_area: '',
    max_area: '',
    min_price: '',
    max_price: '',
    min_lease_price: '',
    max_lease_price: '',
    latitude: '',
    longitude: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFetchFromUrl = async () => {
    if (!naverUrl.trim()) {
      setError('네이버 부동산 URL을 입력하세요');
      return;
    }

    // URL에서 단지 ID 추출
    const match = naverUrl.match(/complexes\/(\d+)/);
    if (!match) {
      setError('유효하지 않은 네이버 부동산 URL입니다');
      return;
    }

    const complexId = match[1];

    // 일단 단지 ID는 바로 채워줌
    setFormData(prev => ({ ...prev, complex_id: complexId }));
    setFetchingInfo(true);
    setError('단지 ID가 추출되었습니다. 추가 정보를 가져오는 중...');

    try {
      const response = await axios.get(`${API_URL}/api/scraper/complex`, {
        params: { url: naverUrl },
        timeout: 25000
      });

      const data = response.data;

      // 폼 데이터 자동 채우기
      setFormData({
        complex_id: data.complex_id || complexId,
        complex_name: data.complex_name || '',
        complex_type: data.complex_type || '',
        total_households: data.total_households?.toString() || '',
        total_dongs: data.total_dongs?.toString() || '',
        completion_date: data.completion_date || '',
        min_area: data.min_area?.toString() || '',
        max_area: data.max_area?.toString() || '',
        min_price: data.min_price?.toString() || '',
        max_price: data.max_price?.toString() || '',
        min_lease_price: data.min_lease_price?.toString() || '',
        max_lease_price: data.max_lease_price?.toString() || '',
        latitude: data.latitude?.toString() || '',
        longitude: data.longitude?.toString() || '',
      });

      setError('');
    } catch (err: any) {
      // 크롤링 실패해도 단지 ID는 이미 채워져 있음
      setError('⚠️ 자동 정보 가져오기 실패. 단지 ID는 입력되었으니 나머지는 수동으로 입력해주세요.');
    } finally {
      setFetchingInfo(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 빈 값 제거 및 숫자 변환
      const payload: any = {
        complex_id: formData.complex_id,
        complex_name: formData.complex_name,
      };

      if (formData.complex_type) payload.complex_type = formData.complex_type;
      if (formData.total_households) payload.total_households = parseInt(formData.total_households);
      if (formData.total_dongs) payload.total_dongs = parseInt(formData.total_dongs);
      if (formData.completion_date) payload.completion_date = formData.completion_date;
      if (formData.min_area) payload.min_area = parseFloat(formData.min_area);
      if (formData.max_area) payload.max_area = parseFloat(formData.max_area);
      if (formData.min_price) payload.min_price = parseInt(formData.min_price);
      if (formData.max_price) payload.max_price = parseInt(formData.max_price);
      if (formData.min_lease_price) payload.min_lease_price = parseInt(formData.min_lease_price);
      if (formData.max_lease_price) payload.max_lease_price = parseInt(formData.max_lease_price);
      if (formData.latitude) payload.latitude = parseFloat(formData.latitude);
      if (formData.longitude) payload.longitude = parseFloat(formData.longitude);

      const response = await axios.post(`${API_URL}/api/complexes/`, payload);

      // 단지 추가 성공 후 백그라운드 크롤링 시작
      const message = collectAddress
        ? '✅ 단지가 추가되었습니다. 백그라운드에서 매물 정보와 주소를 수집합니다...'
        : '✅ 단지가 추가되었습니다. 백그라운드에서 매물 정보를 수집합니다...';
      setError(message);

      // 백그라운드 크롤링 시작 (응답을 기다리지 않음)
      axios.post(`${API_URL}/api/scraper/crawl`, {
        complex_id: response.data.complex_id,
        collect_address: collectAddress
      }).catch(err => {
        console.error('크롤링 실패:', err);
      });

      // 1초 후 페이지 이동
      setTimeout(() => {
        router.push(`/complexes/${response.data.complex_id}`);
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || '단지 추가에 실패했습니다.');
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">새 단지 추가</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow">
          {/* URL 자동 입력 */}
          <div className="border-b pb-4 bg-blue-50 p-4 rounded-md">
            <h2 className="text-xl font-semibold mb-4">🔗 URL에서 자동 입력</h2>
            <p className="text-sm text-gray-600 mb-3">
              네이버 부동산 단지 URL을 붙여넣으면 자동으로 정보를 가져옵니다
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={naverUrl}
                onChange={(e) => setNaverUrl(e.target.value)}
                placeholder="https://new.land.naver.com/complexes/1482"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={handleFetchFromUrl}
                disabled={fetchingInfo}
                className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {fetchingInfo ? '가져오는 중...' : '정보 가져오기'}
              </button>
            </div>
          </div>

          {/* 필수 정보 */}
          <div className="border-b pb-4">
            <h2 className="text-xl font-semibold mb-4">필수 정보</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  단지 ID (네이버) *
                </label>
                <input
                  type="text"
                  name="complex_id"
                  value={formData.complex_id}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="109208"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  단지명 *
                </label>
                <input
                  type="text"
                  name="complex_name"
                  value={formData.complex_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="래미안대치팰리스"
                />
              </div>
            </div>
          </div>

          {/* 선택 정보 */}
          <div className="border-b pb-4">
            <h2 className="text-xl font-semibold mb-4">선택 정보</h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  단지 유형
                </label>
                <input
                  type="text"
                  name="complex_type"
                  value={formData.complex_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="아파트"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  준공일
                </label>
                <input
                  type="text"
                  name="completion_date"
                  value={formData.completion_date}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="2020-03"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  총 세대수
                </label>
                <input
                  type="number"
                  name="total_households"
                  value={formData.total_households}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  총 동수
                </label>
                <input
                  type="number"
                  name="total_dongs"
                  value={formData.total_dongs}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="10"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최소 면적 (㎡)
                </label>
                <input
                  type="number"
                  step="0.01"
                  name="min_area"
                  value={formData.min_area}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="59.0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최대 면적 (㎡)
                </label>
                <input
                  type="number"
                  step="0.01"
                  name="max_area"
                  value={formData.max_area}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="149.0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최소 매매가 (만원)
                </label>
                <input
                  type="number"
                  name="min_price"
                  value={formData.min_price}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="50000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최대 매매가 (만원)
                </label>
                <input
                  type="number"
                  name="max_price"
                  value={formData.max_price}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="150000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최소 전세가 (만원)
                </label>
                <input
                  type="number"
                  name="min_lease_price"
                  value={formData.min_lease_price}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="30000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최대 전세가 (만원)
                </label>
                <input
                  type="number"
                  name="max_lease_price"
                  value={formData.max_lease_price}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="100000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  위도
                </label>
                <input
                  type="number"
                  step="0.000001"
                  name="latitude"
                  value={formData.latitude}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="37.1234"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  경도
                </label>
                <input
                  type="number"
                  step="0.000001"
                  name="longitude"
                  value={formData.longitude}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="127.5678"
                />
              </div>
            </div>
          </div>

          {/* 주소 수집 옵션 */}
          <div className="border-b pb-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={collectAddress}
                onChange={(e) => setCollectAddress(e.target.checked)}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              />
              <div>
                <div className="font-medium text-gray-900">주소도 함께 수집</div>
                <div className="text-sm text-gray-600">
                  매물 검색과 함께 단지 주소를 자동으로 수집합니다 (약 10-15초 소요, 브라우저가 열리고 수동으로 계속 버튼을 눌러야 합니다)
                </div>
              </div>
            </label>
          </div>

          {/* 버튼 */}
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? '추가 중...' : '단지 추가'}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300"
            >
              취소
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
