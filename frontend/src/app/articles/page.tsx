'use client';

import { useEffect, useState } from 'react';
import { articleAPI, complexAPI } from '@/lib/api';
import type { Article, Complex } from '@/types';

export default function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [loading, setLoading] = useState(true);

  // 필터 상태
  const [selectedComplex, setSelectedComplex] = useState<string>('');
  const [selectedTradeType, setSelectedTradeType] = useState<string>('');
  const [minArea, setMinArea] = useState<string>('');
  const [maxArea, setMaxArea] = useState<string>('');

  useEffect(() => {
    const fetchComplexes = async () => {
      try {
        const data = await complexAPI.getList();
        setComplexes(data);
      } catch (error) {
        console.error('단지 로딩 실패:', error);
      }
    };

    fetchComplexes();
  }, []);

  useEffect(() => {
    const fetchArticles = async () => {
      setLoading(true);
      try {
        const params: any = {
          limit: 50,
        };

        if (selectedComplex) params.complex_id = selectedComplex;
        if (selectedTradeType) params.trade_type = selectedTradeType;
        if (minArea) params.min_area = parseFloat(minArea);
        if (maxArea) params.max_area = parseFloat(maxArea);

        const data = await articleAPI.search(params);
        setArticles(data);
      } catch (error) {
        console.error('매물 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, [selectedComplex, selectedTradeType, minArea, maxArea]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900">매물 검색</h1>
        <p className="text-gray-600 mt-2">조건에 맞는 매물을 검색하세요</p>
      </div>

      {/* 필터 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">검색 조건</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">단지</label>
            <select
              value={selectedComplex}
              onChange={(e) => setSelectedComplex(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">전체</option>
              {complexes.map((complex) => (
                <option key={complex.id} value={complex.complex_id}>
                  {complex.complex_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">거래 유형</label>
            <select
              value={selectedTradeType}
              onChange={(e) => setSelectedTradeType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">전체</option>
              <option value="매매">매매</option>
              <option value="전세">전세</option>
              <option value="월세">월세</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">최소 면적(㎡)</label>
            <input
              type="number"
              value={minArea}
              onChange={(e) => setMinArea(e.target.value)}
              placeholder="예: 80"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">최대 면적(㎡)</label>
            <input
              type="number"
              value={maxArea}
              onChange={(e) => setMaxArea(e.target.value)}
              placeholder="예: 130"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* 결과 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            검색 결과 {loading ? '...' : `(${articles.length}건)`}
          </h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-600">로딩 중...</div>
        ) : articles.length === 0 ? (
          <div className="p-8 text-center text-gray-600">검색 결과가 없습니다</div>
        ) : (
          <div className="divide-y">
            {articles.map((article) => (
              <div key={article.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${
                          article.trade_type === '매매'
                            ? 'bg-blue-100 text-blue-800'
                            : article.trade_type === '전세'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-purple-100 text-purple-800'
                        }`}
                      >
                        {article.trade_type}
                      </span>
                      <span className="text-lg font-semibold text-gray-900">{article.price}</span>
                      {article.price_change_state && article.price_change_state !== 'SAME' && (
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            article.price_change_state === 'UP'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {article.price_change_state === 'UP' ? '↑ 상승' : '↓ 하락'}
                        </span>
                      )}
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      {article.area_name} · {article.area1}㎡ · {article.floor_info} · {article.direction}
                    </div>
                    <div className="mt-1 text-sm text-gray-500">{article.building_name}</div>
                    {article.feature_desc && (
                      <div className="mt-2 text-sm text-gray-700">{article.feature_desc}</div>
                    )}
                    <div className="mt-2 text-xs text-gray-500">
                      {article.realtor_name} · {article.confirm_date?.replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
