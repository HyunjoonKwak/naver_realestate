'use client';

import { useEffect, useState } from 'react';
import { complexAPI, articleAPI, transactionAPI } from '@/lib/api';
import type { Complex, Article, Transaction } from '@/types';

export default function Home() {
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [recentArticles, setRecentArticles] = useState<Article[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [complexesData, articlesData, transactionsData] = await Promise.all([
          complexAPI.getList(0, 10),
          articleAPI.getRecent(5),
          transactionAPI.getRecent(5),
        ]);
        setComplexes(complexesData);
        setRecentArticles(articlesData);
        setRecentTransactions(transactionsData);
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
        <p className="text-gray-600">네이버 부동산 매물 및 실거래가 관리 시스템</p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-600">등록된 단지</div>
          <div className="mt-2 text-3xl font-bold text-blue-600">{complexes.length}개</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-600">활성 매물</div>
          <div className="mt-2 text-3xl font-bold text-green-600">{recentArticles.length}건</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-600">실거래가</div>
          <div className="mt-2 text-3xl font-bold text-purple-600">{recentTransactions.length}건</div>
        </div>
      </div>

      {/* 단지 목록 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">단지 목록</h2>
        </div>
        <div className="divide-y">
          {complexes.map((complex) => (
            <a
              key={complex.id}
              href={`/complexes/${complex.complex_id}`}
              className="block px-6 py-4 hover:bg-gray-50 transition"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{complex.complex_name}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {complex.complex_type} · {complex.total_households}세대 · {complex.total_dongs}개동
                  </p>
                </div>
                <div className="text-right">
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
      </div>

      {/* 최근 매물 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">최근 매물</h2>
        </div>
        <div className="divide-y">
          {recentArticles.map((article) => (
            <div key={article.id} className="px-6 py-4">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {article.area_name} · {article.floor_info} · {article.direction}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">{article.building_name}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold text-blue-600">{article.price}</div>
                  <div className="text-xs text-gray-500">{article.trade_type}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 최근 실거래가 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">최근 실거래가</h2>
        </div>
        <div className="divide-y">
          {recentTransactions.map((transaction) => (
            <div key={transaction.id} className="px-6 py-4">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {transaction.area}㎡ · {transaction.floor}층
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {transaction.trade_date?.replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')}
                  </div>
                </div>
                <div className="text-lg font-semibold text-purple-600">{transaction.formatted_price}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
