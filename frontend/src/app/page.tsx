'use client';

import { useEffect, useState } from 'react';
import { complexAPI, articleAPI } from '@/lib/api';
import type { Complex } from '@/types';

interface ComplexStats {
  complex_id: string;
  complex_name: string;
  complex_type: string;
  address: string;
  total_households: number;
  articles: {
    total: number;
    sale: number;
    lease: number;
    monthly: number;
  };
  price_range: {
    sale_min: number | null;
    sale_max: number | null;
    lease_min: number | null;
    lease_max: number | null;
    monthly_deposit_min: number | null;
    monthly_deposit_max: number | null;
    monthly_rent_min: number | null;
    monthly_rent_max: number | null;
  };
  changes_24h: {
    new: number;
    removed: number;
    price_up: number;
    price_down: number;
  };
  min_price: number | null;
  max_price: number | null;
}

export default function Home() {
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [complexStats, setComplexStats] = useState<Record<string, ComplexStats>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await complexAPI.getAll();
      const complexesData = response.data;
      setComplexes(complexesData);

      // 각 단지의 상세 통계 가져오기
      const statsPromises = complexesData.map(async (complex) => {
        try {
          const [statsRes, changesRes] = await Promise.all([
            complexAPI.getStats(complex.complex_id),
            articleAPI.getChangeSummary(complex.complex_id, 24).catch(() => ({
              data: { summary: { new: 0, removed: 0, price_up: 0, price_down: 0 } }
            }))
          ]);

          return {
            complex_id: complex.complex_id,
            complex_name: complex.complex_name,
            complex_type: complex.complex_type,
            address: complex.address,
            total_households: complex.total_households,
            articles: statsRes.data.articles,
            price_range: statsRes.data.price_range,
            changes_24h: changesRes.data.summary,
            min_price: complex.min_price,
            max_price: complex.max_price,
          };
        } catch (err) {
          console.log(`단지 ${complex.complex_id} 통계 로딩 실패`);
          return null;
        }
      });

      const statsResults = await Promise.all(statsPromises);
      const statsMap: Record<string, ComplexStats> = {};
      statsResults.forEach((stat) => {
        if (stat) {
          statsMap[stat.complex_id] = stat;
        }
      });
      setComplexStats(statsMap);
    } catch (error) {
      console.error('데이터 로딩 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTotalArticles = () => {
    return Object.values(complexStats).reduce((sum, stat) => sum + (stat.articles?.total || 0), 0);
  };

  const getTotalChanges = () => {
    return Object.values(complexStats).reduce((sum, stat) => {
      if (!stat.changes_24h) return sum;
      return sum + (stat.changes_24h.new || 0) + (stat.changes_24h.removed || 0) +
             (stat.changes_24h.price_up || 0) + (stat.changes_24h.price_down || 0);
    }, 0);
  };

  const getAverageSalePrice = () => {
    const prices = Object.values(complexStats)
      .filter(stat => stat.price_range && stat.price_range.sale_min && stat.price_range.sale_max)
      .map(stat => ((stat.price_range.sale_min! + stat.price_range.sale_max!) / 2));

    if (prices.length === 0) return 0;
    return prices.reduce((sum, price) => sum + price, 0) / prices.length;
  };

  const formatPrice = (price: number | null) => {
    if (!price) return '-';
    if (price >= 10000) {
      return `${(price / 10000).toFixed(1)}억`;
    }
    return `${price.toLocaleString()}만`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-xl text-gray-600">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">부동산 관리 대시보드</h1>
        <p className="text-blue-100">네이버 부동산 매물 실시간 모니터링</p>
      </div>

      {/* 전체 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-600">등록 단지</div>
              <div className="mt-2 text-3xl font-bold text-gray-900">{complexes.length}</div>
              <div className="mt-1 text-xs text-gray-500">개 단지</div>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-600">전체 매물</div>
              <div className="mt-2 text-3xl font-bold text-gray-900">{getTotalArticles()}</div>
              <div className="mt-1 text-xs text-gray-500">건</div>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-600">24시간 변경</div>
              <div className="mt-2 text-3xl font-bold text-gray-900">{getTotalChanges()}</div>
              <div className="mt-1 text-xs text-gray-500">건</div>
            </div>
            <div className="p-3 bg-yellow-100 rounded-full">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-600">평균 매매가</div>
              <div className="mt-2 text-3xl font-bold text-gray-900">
                {formatPrice(getAverageSalePrice())}
              </div>
              <div className="mt-1 text-xs text-gray-500">단지별 평균</div>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* 단지별 상세 카드 */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">단지별 현황</h2>
          <a
            href="/complexes/new"
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            단지 추가
          </a>
        </div>

        {complexes.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <p className="text-gray-500 text-lg mb-4">등록된 단지가 없습니다.</p>
            <a
              href="/complexes/new"
              className="inline-block text-blue-600 hover:text-blue-700 font-medium"
            >
              첫 단지를 추가해보세요 →
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {complexes.map((complex) => {
              const stats = complexStats[complex.complex_id];
              if (!stats) return null;

              const hasChanges = stats.changes_24h && (
                                stats.changes_24h.new > 0 ||
                                stats.changes_24h.removed > 0 ||
                                stats.changes_24h.price_up > 0 ||
                                stats.changes_24h.price_down > 0
                              );

              return (
                <a
                  key={complex.complex_id}
                  href={`/complexes/${complex.complex_id}`}
                  className="block bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 overflow-hidden"
                >
                  {/* 헤더 */}
                  <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="text-xl font-bold text-gray-900">{stats.complex_name}</h3>
                        <div className="text-sm text-gray-600 mt-1 flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          {stats.address}
                        </div>
                        {stats.total_households && (
                          <div className="text-xs text-gray-500 mt-1">
                            총 {stats.total_households?.toLocaleString()}세대
                          </div>
                        )}
                      </div>
                      {hasChanges && (
                        <div className="ml-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            변경있음
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 통계 그리드 */}
                  <div className="p-6">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      {/* 매물 수 */}
                      <div className="bg-blue-50 rounded-lg p-4">
                        <div className="text-xs text-blue-600 font-medium mb-1">총 매물</div>
                        <div className="text-2xl font-bold text-blue-900">{stats.articles?.total || 0}</div>
                        <div className="text-xs text-blue-600 mt-1">
                          매매 {stats.articles?.sale || 0} · 전세 {stats.articles?.lease || 0} · 월세 {stats.articles?.monthly || 0}
                        </div>
                      </div>

                      {/* 매매 가격 */}
                      <div className="bg-green-50 rounded-lg p-4">
                        <div className="text-xs text-green-600 font-medium mb-1">매매 가격</div>
                        <div className="text-lg font-bold text-green-900">
                          {formatPrice(stats.price_range?.sale_min || null)}
                        </div>
                        <div className="text-xs text-green-600 mt-1">
                          ~ {formatPrice(stats.price_range?.sale_max || null)}
                        </div>
                      </div>

                      {/* 전세 가격 */}
                      <div className="bg-purple-50 rounded-lg p-4">
                        <div className="text-xs text-purple-600 font-medium mb-1">전세 가격</div>
                        <div className="text-lg font-bold text-purple-900">
                          {formatPrice(stats.price_range?.lease_min || null)}
                        </div>
                        <div className="text-xs text-purple-600 mt-1">
                          ~ {formatPrice(stats.price_range?.lease_max || null)}
                        </div>
                      </div>

                      {/* 월세 가격 */}
                      <div className="bg-yellow-50 rounded-lg p-4">
                        <div className="text-xs text-yellow-600 font-medium mb-1">월세</div>
                        {stats.price_range?.monthly_deposit_min || stats.price_range?.monthly_rent_min ? (
                          <div>
                            <div className="text-sm font-bold text-yellow-900">
                              보증금 {formatPrice(stats.price_range?.monthly_deposit_min)}
                            </div>
                            <div className="text-xs text-yellow-600 mt-0.5">
                              ~ {formatPrice(stats.price_range?.monthly_deposit_max)}
                            </div>
                            {stats.price_range?.monthly_rent_min && (
                              <div className="text-sm font-bold text-yellow-900 mt-2">
                                월세 {formatPrice(stats.price_range?.monthly_rent_min)}
                              </div>
                            )}
                            {stats.price_range?.monthly_rent_max && (
                              <div className="text-xs text-yellow-600 mt-0.5">
                                ~ {formatPrice(stats.price_range?.monthly_rent_max)}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="text-lg font-bold text-yellow-900">-</div>
                        )}
                      </div>
                    </div>

                    {/* 24시간 변경 사항 */}
                    {hasChanges && stats.changes_24h && (
                      <div className="border-t pt-4">
                        <div className="text-xs font-medium text-gray-600 mb-2">24시간 변경사항</div>
                        <div className="flex gap-2 flex-wrap">
                          {stats.changes_24h.new > 0 && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              신규 {stats.changes_24h.new}
                            </span>
                          )}
                          {stats.changes_24h.removed > 0 && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              삭제 {stats.changes_24h.removed}
                            </span>
                          )}
                          {stats.changes_24h.price_up > 0 && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              ↑ {stats.changes_24h.price_up}
                            </span>
                          )}
                          {stats.changes_24h.price_down > 0 && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              ↓ {stats.changes_24h.price_down}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* 더보기 링크 */}
                    <div className="mt-4 pt-4 border-t flex items-center justify-between">
                      <span className="text-sm text-gray-500">{stats.complex_type}</span>
                      <span className="text-sm text-blue-600 font-medium flex items-center gap-1">
                        상세보기
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </span>
                    </div>
                  </div>
                </a>
              );
            })}
          </div>
        )}
      </div>

      {/* 빠른 액션 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">빠른 작업</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <a href="/complexes" className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <div>
              <div className="text-sm font-medium text-gray-900">단지 관리</div>
              <div className="text-xs text-gray-600">전체 목록</div>
            </div>
          </a>

          <a href="/articles" className="flex items-center gap-3 p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <div className="text-sm font-medium text-gray-900">매물 검색</div>
              <div className="text-xs text-gray-600">전체 매물</div>
            </div>
          </a>

          <a href="/transactions" className="flex items-center gap-3 p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div className="text-sm font-medium text-gray-900">실거래가</div>
              <div className="text-xs text-gray-600">거래 내역</div>
            </div>
          </a>

          <a href="/scheduler" className="flex items-center gap-3 p-4 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors">
            <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div className="text-sm font-medium text-gray-900">스케줄러</div>
              <div className="text-xs text-gray-600">자동 크롤링</div>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
