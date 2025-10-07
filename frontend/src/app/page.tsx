'use client';

import { useEffect, useState } from 'react';
import { complexAPI } from '@/lib/api';
import type { Complex } from '@/types';

export default function Home() {
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [totalArticles, setTotalArticles] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await complexAPI.getAll();
        const complexesData = response.data;
        setComplexes(complexesData);

        // 각 단지의 통계를 가져와서 총 매물 수 계산
        let totalCount = 0;
        for (const complex of complexesData) {
          try {
            const statsRes = await complexAPI.getStats(complex.complex_id);
            totalCount += statsRes.data.articles.total;
          } catch (err) {
            console.log(`단지 ${complex.complex_id} 통계 로딩 실패`);
          }
        }
        setTotalArticles(totalCount);
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-xl text-gray-600">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">대시보드</h1>
        <p className="text-gray-600">네이버 부동산 매물 관리 시스템</p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-600">등록된 단지</div>
          <div className="mt-2 text-3xl font-bold text-blue-600">{complexes.length}개</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-600">전체 매물</div>
          <div className="mt-2 text-3xl font-bold text-green-600">{totalArticles}건</div>
        </div>
      </div>

      {/* 단지 목록 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">단지 목록</h2>
          <a
            href="/complexes/new"
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
          >
            단지 추가
          </a>
        </div>
        {complexes.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500">등록된 단지가 없습니다.</p>
            <a
              href="/complexes/new"
              className="inline-block mt-4 text-blue-600 hover:text-blue-700"
            >
              첫 단지를 추가해보세요 →
            </a>
          </div>
        ) : (
          <div className="divide-y">
            {complexes.map((complex) => (
              <a
                key={complex.id}
                href={`/complexes/${complex.complex_id}`}
                className="block px-6 py-4 hover:bg-gray-50 transition"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900">{complex.complex_name}</h3>
                    {complex.address && (
                      <div className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {complex.address}
                      </div>
                    )}
                    <p className="text-sm text-gray-600 mt-1">
                      {complex.complex_type || '-'} · {complex.total_households || '-'}세대 · {complex.total_dongs || '-'}개동
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-sm font-medium text-blue-600">
                      {complex.min_price && complex.max_price
                        ? `${(complex.min_price / 10000).toFixed(1)}억 ~ ${(complex.max_price / 10000).toFixed(1)}억`
                        : '-'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">매매가</div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
