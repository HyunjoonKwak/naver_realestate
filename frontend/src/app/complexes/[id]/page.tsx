'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { complexAPI, articleAPI, scraperAPI } from '@/lib/api';
import type { ComplexDetail, ComplexStats, ArticleChangeSummary, ArticleChangeList } from '@/types';

export default function ComplexDetailPage() {
  const params = useParams();
  const router = useRouter();
  const complexId = params.id as string;

  const [complex, setComplex] = useState<ComplexDetail | null>(null);
  const [stats, setStats] = useState<ComplexStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // 변동사항 상태
  const [changeSummary, setChangeSummary] = useState<ArticleChangeSummary | null>(null);
  const [changeList, setChangeList] = useState<ArticleChangeList | null>(null);
  const [showChangeDetails, setShowChangeDetails] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null);

  // 필터 상태
  const [selectedTradeType, setSelectedTradeType] = useState<string>('all');
  const [selectedAreaName, setSelectedAreaName] = useState<string>('all');
  const [selectedBuilding, setSelectedBuilding] = useState<string>('all');

  // 정렬 상태
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [complexRes, statsRes] = await Promise.all([
          complexAPI.getDetail(complexId),
          complexAPI.getStats(complexId),
        ]);
        setComplex(complexRes.data);
        setStats(statsRes.data);

        // localStorage에서 마지막 새로고침 시각 불러오기
        const savedTime = localStorage.getItem(`lastRefresh_${complexId}`);
        if (savedTime) {
          setLastRefreshTime(new Date(savedTime));
        }

        // 크롤링 진행 중인지 확인하고 폴링 시작
        checkAndPollRefreshStatus();

        // 변동사항 조회 (24시간 이내)
        try {
          const [summaryRes, listRes] = await Promise.all([
            articleAPI.getChangeSummary(complexId, 24),
            articleAPI.getChangeList(complexId, 24, 10)
          ]);
          setChangeSummary(summaryRes.data);
          setChangeList(listRes.data);
        } catch (err) {
          console.log('변동사항 조회 실패 (아직 스냅샷이 없을 수 있음)');
        }
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [complexId]);

  const handleRefresh = async () => {
    console.log('[DEBUG] handleRefresh 실행 - Version 2.0 with refresh API');
    console.log('[DEBUG] complexId:', complexId);
    setRefreshing(true);
    try {
      // 새로고침 시작
      console.log('[DEBUG] Calling scraperAPI.refresh...');
      await scraperAPI.refresh(complexId);
      console.log('[DEBUG] scraperAPI.refresh 완료');
      const now = new Date();
      setLastRefreshTime(now);
      // localStorage에 저장
      localStorage.setItem(`lastRefresh_${complexId}`, now.toISOString());

      // 폴링으로 크롤링 완료 대기
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await scraperAPI.getRefreshStatus(complexId);
          const status = statusRes.data.status;

          if (status === 'completed') {
            clearInterval(pollInterval);

            // 크롤링 완료 후 데이터 다시 로드
            const [complexRes, statsRes, summaryRes, listRes] = await Promise.all([
              complexAPI.getDetail(complexId),
              complexAPI.getStats(complexId),
              articleAPI.getChangeSummary(complexId, 24),
              articleAPI.getChangeList(complexId, 24, 10)
            ]);
            setComplex(complexRes.data);
            setStats(statsRes.data);
            setChangeSummary(summaryRes.data);
            setChangeList(listRes.data);
            setRefreshing(false);
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            alert('크롤링에 실패했습니다.');
            setRefreshing(false);
          }
        } catch (err) {
          console.error('상태 조회 실패:', err);
        }
      }, 2000); // 2초마다 상태 확인

      // 최대 5분 타임아웃
      setTimeout(() => {
        clearInterval(pollInterval);
        if (refreshing) {
          setRefreshing(false);
          alert('크롤링 시간이 초과되었습니다.');
        }
      }, 300000);

    } catch (error: any) {
      console.error('새로고침 실패:', error);
      alert(error.response?.data?.detail || '새로고침에 실패했습니다.');
      setRefreshing(false);
    }
  };

  const checkAndPollRefreshStatus = async () => {
    try {
      const statusRes = await scraperAPI.getRefreshStatus(complexId);
      const status = statusRes.data.status;

      if (status === 'running') {
        console.log('[AUTO-REFRESH] 크롤링이 진행 중입니다. 폴링을 시작합니다.');
        setRefreshing(true);
        pollRefreshStatus();
      }
    } catch (err) {
      console.log('[AUTO-REFRESH] 크롤링 상태 조회 실패 또는 크롤링 기록 없음');
    }
  };

  const pollRefreshStatus = () => {
    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await scraperAPI.getRefreshStatus(complexId);
        const status = statusRes.data.status;

        if (status === 'completed') {
          console.log('[AUTO-REFRESH] 크롤링 완료. 데이터를 다시 로드합니다.');
          clearInterval(pollInterval);
          await reloadAllData();
          setRefreshing(false);
        } else if (status === 'failed') {
          console.log('[AUTO-REFRESH] 크롤링 실패');
          clearInterval(pollInterval);
          setRefreshing(false);
        }
      } catch (err) {
        console.error('[AUTO-REFRESH] 상태 조회 실패:', err);
      }
    }, 2000);

    // 최대 5분 타임아웃
    setTimeout(() => {
      clearInterval(pollInterval);
      setRefreshing(false);
    }, 300000);
  };

  const reloadAllData = async () => {
    try {
      const [complexRes, statsRes, summaryRes, listRes] = await Promise.all([
        complexAPI.getDetail(complexId),
        complexAPI.getStats(complexId),
        articleAPI.getChangeSummary(complexId, 24),
        articleAPI.getChangeList(complexId, 24, 10),
      ]);
      setComplex(complexRes.data);
      setStats(statsRes.data);
      setChangeSummary(summaryRes.data);
      setChangeList(listRes.data);
      console.log('[AUTO-REFRESH] 데이터 리로드 완료');
    } catch (err) {
      console.error('[AUTO-REFRESH] 데이터 리로드 실패:', err);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`${complex?.complex_name} 단지를 삭제하시겠습니까?\n\n단지와 관련된 모든 매물 및 실거래가 데이터가 함께 삭제됩니다.`)) {
      return;
    }

    setDeleting(true);
    try {
      await complexAPI.delete(complexId);
      alert('단지가 삭제되었습니다.');
      router.push('/complexes');
    } catch (error: any) {
      alert(error.response?.data?.detail || '단지 삭제에 실패했습니다.');
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-xl text-gray-600">로딩 중...</div>
      </div>
    );
  }

  if (!complex) {
    return (
      <div className="text-center py-12">
        <div className="text-xl text-gray-600">단지를 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 단지 헤더 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{complex.complex_name}</h1>
            <a
              href={`https://new.land.naver.com/complexes/${complexId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-md hover:bg-green-100 transition-colors"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              네이버 부동산
            </a>
          </div>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
          >
            {deleting ? '삭제 중...' : '단지 삭제'}
          </button>
        </div>
        <div className="mt-3 space-y-2">
          {/* 도로명 주소 */}
          {complex.road_address && (
            <div className="flex items-center gap-2">
              <div className="text-gray-600 text-sm flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="font-medium text-blue-600">[도로명]</span>
                {complex.road_address}
              </div>
            </div>
          )}

          {/* 지번(법정동) 주소 */}
          {complex.jibun_address && (
            <div className="flex items-center gap-2">
              <div className="text-gray-600 text-sm flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="font-medium text-green-600">[법정동]</span>
                {complex.jibun_address}
              </div>
            </div>
          )}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-4">
          <div>
            <div className="text-gray-600">유형</div>
            <div className="font-medium">{complex.complex_type}</div>
          </div>
          <div>
            <div className="text-gray-600">세대수</div>
            <div className="font-medium">{complex.total_households}세대</div>
          </div>
          <div>
            <div className="text-gray-600">동수</div>
            <div className="font-medium">{complex.total_dongs}개동</div>
          </div>
          <div>
            <div className="text-gray-600">준공일</div>
            <div className="font-medium">
              {complex.completion_date?.replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')}
            </div>
          </div>
        </div>
      </div>

      {/* 통계 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-sm font-medium text-gray-600">전체 매물</div>
            <div className="mt-2 text-3xl font-bold text-blue-600">{stats.articles.total}건</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-sm font-medium text-gray-600">매매</div>
            <div className="mt-2 text-3xl font-bold text-green-600">{stats.articles.sale}건</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-sm font-medium text-gray-600">전세</div>
            <div className="mt-2 text-3xl font-bold text-purple-600">{stats.articles.lease}건</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-sm font-medium text-gray-600">월세</div>
            <div className="mt-2 text-3xl font-bold text-orange-600">{stats.articles.monthly}건</div>
          </div>
        </div>
      )}

      {/* 면적별 가격 정보 */}
      {complex.articles && complex.articles.length > 0 && (() => {
        // 면적별 가격 통계 계산
        const areaPriceMap = new Map<string, { sale: number[], lease: number[] }>();

        complex.articles.forEach(article => {
          if (!article.area_name || !article.price) return;

          if (!areaPriceMap.has(article.area_name)) {
            areaPriceMap.set(article.area_name, { sale: [], lease: [] });
          }

          const priceData = areaPriceMap.get(article.area_name)!;
          const priceStr = article.price.replace(/[^0-9]/g, '');
          const price = parseInt(priceStr);

          if (!isNaN(price)) {
            if (article.trade_type === '매매') {
              priceData.sale.push(price);
            } else if (article.trade_type === '전세') {
              priceData.lease.push(price);
            }
          }
        });

        // 정렬된 면적 목록
        const sortedAreas = Array.from(areaPriceMap.keys()).sort();

        return (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-semibold text-gray-900">면적별 가격 정보</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sortedAreas.map(areaName => {
                  const priceData = areaPriceMap.get(areaName)!;

                  return (
                    <div key={areaName} className="border rounded-lg p-4">
                      <div className="text-lg font-semibold text-gray-900 mb-3">{areaName}</div>

                      <div className="grid grid-cols-2 gap-4">
                        {/* 매매 */}
                        <div>
                          <div className="text-xs text-gray-500 mb-2">매매</div>
                          {priceData.sale.length > 0 ? (
                            <>
                              <div className="text-sm mb-1">
                                <span className="text-xs text-gray-600">최저 </span>
                                <span className="font-medium text-blue-600">{Math.min(...priceData.sale).toLocaleString()}만</span>
                              </div>
                              <div className="text-sm">
                                <span className="text-xs text-gray-600">최고 </span>
                                <span className="font-medium text-blue-600">{Math.max(...priceData.sale).toLocaleString()}만</span>
                              </div>
                            </>
                          ) : (
                            <div className="text-sm text-gray-400">-</div>
                          )}
                        </div>

                        {/* 전세 */}
                        <div>
                          <div className="text-xs text-gray-500 mb-2">전세</div>
                          {priceData.lease.length > 0 ? (
                            <>
                              <div className="text-sm mb-1">
                                <span className="text-xs text-gray-600">최저 </span>
                                <span className="font-medium text-green-600">{Math.min(...priceData.lease).toLocaleString()}만</span>
                              </div>
                              <div className="text-sm">
                                <span className="text-xs text-gray-600">최고 </span>
                                <span className="font-medium text-green-600">{Math.max(...priceData.lease).toLocaleString()}만</span>
                              </div>
                            </>
                          ) : (
                            <div className="text-sm text-gray-400">-</div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })()}

      {/* 최근 매매 실거래가 정보 */}
      {stats && stats.transactions.recent && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b bg-gradient-to-r from-green-50 to-emerald-50">
            <h2 className="text-xl font-semibold text-gray-900">최근 매매 실거래가</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-sm text-gray-600 mb-2">거래가</div>
                <div className="text-2xl font-bold text-green-600">{stats.transactions.recent.formatted_price}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600 mb-2">거래일</div>
                <div className="text-xl font-semibold text-gray-900">
                  {stats.transactions.recent.trade_date?.replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')}
                </div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600 mb-2">전용면적</div>
                <div className="text-xl font-semibold text-gray-900">
                  {stats.transactions.recent.exclusive_area}㎡
                </div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600 mb-2">층</div>
                <div className="text-xl font-semibold text-gray-900">
                  {stats.transactions.recent.floor}층
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 매물 목록 */}
      {complex.articles && complex.articles.length > 0 && (() => {
        // 고유한 거래유형, 평형, 동 목록 추출
        const tradeTypes = Array.from(new Set(complex.articles.map(a => a.trade_type).filter(Boolean)));
        const areaNames = Array.from(new Set(complex.articles.map(a => a.area_name).filter(Boolean))).sort();
        const buildings = Array.from(new Set(complex.articles.map(a => a.building_name).filter(Boolean))).sort();

        // 정렬 핸들러
        const handleSort = (column: string) => {
          if (sortColumn === column) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
          } else {
            setSortColumn(column);
            setSortDirection('asc');
          }
        };

        // 필터링된 매물
        let filteredArticles = complex.articles.filter(article => {
          if (selectedTradeType !== 'all' && article.trade_type !== selectedTradeType) return false;
          if (selectedAreaName !== 'all' && article.area_name !== selectedAreaName) return false;
          if (selectedBuilding !== 'all' && article.building_name !== selectedBuilding) return false;
          return true;
        });

        // 정렬 적용
        if (sortColumn) {
          filteredArticles = [...filteredArticles].sort((a, b) => {
            let aValue: any = null;
            let bValue: any = null;

            switch (sortColumn) {
              case 'trade_type':
                aValue = a.trade_type || '';
                bValue = b.trade_type || '';
                break;
              case 'area_name':
                aValue = a.area_name || '';
                bValue = b.area_name || '';
                break;
              case 'building_name':
                aValue = a.building_name || '';
                bValue = b.building_name || '';
                break;
              case 'confirm_date':
                aValue = a.confirm_date || '';
                bValue = b.confirm_date || '';
                break;
            }

            if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
            if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
            return 0;
          });
        }

        return (
          <>
            {/* 변동사항 요약 카드 */}
            {changeSummary && changeSummary.summary.total > 0 && (
              <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
                <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <h2 className="text-xl font-semibold text-gray-900">📊 매물 변동 현황</h2>
                      {lastRefreshTime && (
                        <span className="text-sm text-gray-500">
                          (마지막 갱신: {Math.floor((Date.now() - lastRefreshTime.getTime()) / 60000)}분 전)
                        </span>
                      )}
                    </div>
                    <button
                      onClick={handleRefresh}
                      disabled={refreshing}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                    >
                      <svg className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {refreshing ? '새로고침 중...' : '새로고침'}
                    </button>
                  </div>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    {changeSummary.summary.new > 0 && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="text-sm text-green-600 font-medium mb-1">🆕 신규</div>
                        <div className="text-2xl font-bold text-green-700">{changeSummary.summary.new}건</div>
                      </div>
                    )}
                    {changeSummary.summary.removed > 0 && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <div className="text-sm text-gray-600 font-medium mb-1">🗑️ 소멸</div>
                        <div className="text-2xl font-bold text-gray-700">{changeSummary.summary.removed}건</div>
                      </div>
                    )}
                    {changeSummary.summary.price_up > 0 && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="text-sm text-red-600 font-medium mb-1">📈 가격↑</div>
                        <div className="text-2xl font-bold text-red-700">{changeSummary.summary.price_up}건</div>
                      </div>
                    )}
                    {changeSummary.summary.price_down > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="text-sm text-blue-600 font-medium mb-1">📉 가격↓</div>
                        <div className="text-2xl font-bold text-blue-700">{changeSummary.summary.price_down}건</div>
                      </div>
                    )}
                  </div>

                  {changeSummary.summary.most_significant_change && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-3">
                      <div className="text-sm text-yellow-800">
                        💡 최근 변화: {changeSummary.summary.most_significant_change.building_name} {changeSummary.summary.most_significant_change.floor_info} 가격{' '}
                        {changeSummary.summary.most_significant_change.change_type === 'PRICE_UP' ? '상승' : '하락'}{' '}
                        ({changeSummary.summary.most_significant_change.price_change_percent?.toFixed(1)}%)
                      </div>
                    </div>
                  )}

                  {changeList && changeList.total > 0 && (
                    <button
                      onClick={() => setShowChangeDetails(!showChangeDetails)}
                      className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      상세 보기 {showChangeDetails ? '▲' : '▼'}
                    </button>
                  )}

                  {showChangeDetails && changeList && (
                    <div className="mt-4 border-t pt-4">
                      <div className="space-y-2">
                        {changeList.changes.map((change) => (
                          <div key={change.id} className="flex items-center justify-between text-sm border-b pb-2">
                            <div className="flex items-center gap-3">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                change.change_type === 'NEW' ? 'bg-green-100 text-green-800' :
                                change.change_type === 'REMOVED' ? 'bg-gray-100 text-gray-800' :
                                change.change_type === 'PRICE_UP' ? 'bg-red-100 text-red-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {change.change_type === 'NEW' ? '신규' :
                                 change.change_type === 'REMOVED' ? '소멸' :
                                 change.change_type === 'PRICE_UP' ? '가격↑' : '가격↓'}
                              </span>
                              <span className="text-gray-700">
                                {change.building_name} {change.floor_info} {change.area_name}
                              </span>
                              {(change.change_type === 'PRICE_UP' || change.change_type === 'PRICE_DOWN') && (
                                <span className="text-gray-600">
                                  {change.old_price} → {change.new_price} ({change.price_change_percent?.toFixed(1)}%)
                                </span>
                              )}
                              {change.change_type === 'NEW' && (
                                <span className="text-gray-600">{change.new_price}</span>
                              )}
                            </div>
                            <div className="text-xs text-gray-400">
                              {new Date(change.detected_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b">
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-semibold text-gray-900">
                      현재 매물 ({filteredArticles.length}/{complex.articles.length}건)
                    </h2>
                    {lastRefreshTime && (
                      <span className="text-sm text-gray-500">
                        (마지막 갱신: {Math.floor((Date.now() - lastRefreshTime.getTime()) / 60000)}분 전)
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleRefresh}
                      disabled={refreshing}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                    >
                      <svg className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {refreshing ? '새로고침 중...' : '새로고침'}
                    </button>
                    <button
                      onClick={() => {
                        setSelectedTradeType('all');
                        setSelectedAreaName('all');
                        setSelectedBuilding('all');
                      }}
                      className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 border border-gray-300 rounded-md"
                    >
                      필터 초기화
                    </button>
                  </div>
                </div>

                {/* 필터 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 거래유형 필터 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">거래유형</label>
                  <select
                    value={selectedTradeType}
                    onChange={(e) => setSelectedTradeType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">전체</option>
                    {tradeTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                {/* 평형 필터 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">평형</label>
                  <select
                    value={selectedAreaName}
                    onChange={(e) => setSelectedAreaName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">전체</option>
                    {areaNames.map(name => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                </div>

                {/* 동 필터 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">동</label>
                  <select
                    value={selectedBuilding}
                    onChange={(e) => setSelectedBuilding(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">전체</option>
                    {buildings.map(building => (
                      <option key={building} value={building}>{building}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    onClick={() => handleSort('trade_type')}
                  >
                    <div className="flex items-center gap-1">
                      거래유형
                      <span className="text-gray-400">
                        {sortColumn === 'trade_type' ? (sortDirection === 'asc' ? '↑' : '↓') : '⇅'}
                      </span>
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">가격</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">면적</th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    onClick={() => handleSort('area_name')}
                  >
                    <div className="flex items-center gap-1">
                      평형
                      <span className="text-gray-400">
                        {sortColumn === 'area_name' ? (sortDirection === 'asc' ? '↑' : '↓') : '⇅'}
                      </span>
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    onClick={() => handleSort('building_name')}
                  >
                    <div className="flex items-center gap-1">
                      동
                      <span className="text-gray-400">
                        {sortColumn === 'building_name' ? (sortDirection === 'asc' ? '↑' : '↓') : '⇅'}
                      </span>
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">층</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">방향</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">중개사</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">중복</th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    onClick={() => handleSort('confirm_date')}
                  >
                    <div className="flex items-center gap-1">
                      확인매물
                      <span className="text-gray-400">
                        {sortColumn === 'confirm_date' ? (sortDirection === 'asc' ? '↑' : '↓') : '⇅'}
                      </span>
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">수집일시</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredArticles.map((article) => (
                  <tr key={article.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        article.trade_type === '매매' ? 'bg-blue-100 text-blue-800' :
                        article.trade_type === '전세' ? 'bg-green-100 text-green-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {article.trade_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-gray-900">{article.price}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.area1}㎡</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.area_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.building_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.floor_info}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.direction}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.realtor_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {article.same_addr_cnt && article.same_addr_cnt > 1 ? (
                        <span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded text-xs font-medium">
                          {article.same_addr_cnt}곳
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {article.confirm_date ? (
                        <div className="flex items-center gap-1">
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs font-medium">
                            ✓
                          </span>
                          <span className="text-gray-700 text-xs">
                            {article.confirm_date.slice(0, 4)}.{article.confirm_date.slice(4, 6)}.{article.confirm_date.slice(6, 8)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {article.created_at ? new Date(article.created_at).toLocaleString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      }) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
          </>
        );
      })()}

    </div>
  );
}
