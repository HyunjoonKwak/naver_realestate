'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { complexAPI } from '@/lib/api';
import type { ComplexDetail, ComplexStats } from '@/types';

export default function ComplexDetailPage() {
  const params = useParams();
  const router = useRouter();
  const complexId = params.id as string;

  const [complex, setComplex] = useState<ComplexDetail | null>(null);
  const [stats, setStats] = useState<ComplexStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  // 필터 상태
  const [selectedTradeType, setSelectedTradeType] = useState<string>('all');
  const [selectedAreaName, setSelectedAreaName] = useState<string>('all');
  const [selectedBuilding, setSelectedBuilding] = useState<string>('all');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [complexRes, statsRes] = await Promise.all([
          complexAPI.getDetail(complexId),
          complexAPI.getStats(complexId),
        ]);
        setComplex(complexRes.data);
        setStats(statsRes.data);
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [complexId]);

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
          <h1 className="text-3xl font-bold text-gray-900">{complex.complex_name}</h1>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
          >
            {deleting ? '삭제 중...' : '단지 삭제'}
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">전체 매물</div>
            <div className="mt-2 text-3xl font-bold text-blue-600">{stats.articles.total}건</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">매매</div>
            <div className="mt-2 text-3xl font-bold text-green-600">{stats.articles.sale}건</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">전세</div>
            <div className="mt-2 text-3xl font-bold text-purple-600">{stats.articles.lease}건</div>
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

      {/* 매물 목록 */}
      {complex.articles && complex.articles.length > 0 && (() => {
        // 고유한 거래유형, 평형, 동 목록 추출
        const tradeTypes = Array.from(new Set(complex.articles.map(a => a.trade_type).filter(Boolean)));
        const areaNames = Array.from(new Set(complex.articles.map(a => a.area_name).filter(Boolean))).sort();
        const buildings = Array.from(new Set(complex.articles.map(a => a.building_name).filter(Boolean))).sort();

        // 필터링된 매물
        const filteredArticles = complex.articles.filter(article => {
          if (selectedTradeType !== 'all' && article.trade_type !== selectedTradeType) return false;
          if (selectedAreaName !== 'all' && article.area_name !== selectedAreaName) return false;
          if (selectedBuilding !== 'all' && article.building_name !== selectedBuilding) return false;
          return true;
        });

        return (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  현재 매물 ({filteredArticles.length}/{complex.articles.length}건)
                </h2>
                <button
                  onClick={() => {
                    setSelectedTradeType('all');
                    setSelectedAreaName('all');
                    setSelectedBuilding('all');
                  }}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  필터 초기화
                </button>
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
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">거래유형</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">가격</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">면적</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">평형</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">층</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">방향</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">동</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">중개사</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">중복</th>
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
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.floor_info}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.direction}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{article.building_name}</td>
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
        );
      })()}

    </div>
  );
}
