'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { complexAPI, transactionAPI } from '@/lib/api';
import type { ComplexDetail, ComplexStats, PriceTrend } from '@/types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ComplexDetailPage() {
  const params = useParams();
  const complexId = params.id as string;

  const [complex, setComplex] = useState<ComplexDetail | null>(null);
  const [stats, setStats] = useState<ComplexStats | null>(null);
  const [priceTrend, setPriceTrend] = useState<PriceTrend | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [complexData, statsData, trendData] = await Promise.all([
          complexAPI.getDetail(complexId),
          complexAPI.getStats(complexId),
          transactionAPI.getPriceTrend(complexId, 12),
        ]);
        setComplex(complexData);
        setStats(statsData);
        setPriceTrend(trendData);
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [complexId]);

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
        <h1 className="text-3xl font-bold text-gray-900 mb-4">{complex.complex_name}</h1>
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

      {/* 가격 추이 차트 */}
      {priceTrend && priceTrend.trend.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">가격 추이</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={priceTrend.trend.reverse()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tickFormatter={(value) => value.replace(/(\d{4})(\d{2})/, '$1.$2')} />
              <YAxis tickFormatter={(value) => `${(value / 10000).toFixed(1)}억`} />
              <Tooltip
                formatter={(value: number) => [`${(value / 10000).toFixed(2)}억`, '']}
                labelFormatter={(label) => label.replace(/(\d{4})(\d{2})/, '$1년 $2월')}
              />
              <Legend />
              <Line type="monotone" dataKey="avg_price" stroke="#3b82f6" name="평균" />
              <Line type="monotone" dataKey="max_price" stroke="#ef4444" name="최고" />
              <Line type="monotone" dataKey="min_price" stroke="#10b981" name="최저" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 매물 목록 */}
      {complex.articles && complex.articles.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-xl font-semibold text-gray-900">현재 매물</h2>
          </div>
          <div className="divide-y">
            {complex.articles.map((article) => (
              <div key={article.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        article.trade_type === '매매' ? 'bg-blue-100 text-blue-800' :
                        article.trade_type === '전세' ? 'bg-green-100 text-green-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {article.trade_type}
                      </span>
                      <span className="text-lg font-semibold text-gray-900">{article.price}</span>
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      {article.area_name} · {article.area1}㎡ · {article.floor_info} · {article.direction}
                    </div>
                    <div className="mt-1 text-sm text-gray-500">{article.building_name}</div>
                    {article.feature_desc && (
                      <div className="mt-2 text-sm text-gray-700">{article.feature_desc}</div>
                    )}
                    <div className="mt-2 text-xs text-gray-500">{article.realtor_name}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 실거래가 */}
      {complex.transactions && complex.transactions.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-xl font-semibold text-gray-900">실거래가</h2>
          </div>
          <div className="divide-y">
            {complex.transactions.map((transaction) => (
              <div key={transaction.id} className="px-6 py-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {transaction.area}㎡ (전용 {transaction.exclusive_area}㎡) · {transaction.floor}층
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {transaction.trade_date?.replace(/(\d{4})(\d{2})(\d{2})/, '$1년 $2월 $3일')}
                    </div>
                  </div>
                  <div className="text-lg font-semibold text-purple-600">{transaction.formatted_price}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
