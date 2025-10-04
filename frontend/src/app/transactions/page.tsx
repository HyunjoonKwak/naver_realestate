'use client';

import { useEffect, useState } from 'react';
import { transactionAPI, complexAPI } from '@/lib/api';
import type { Transaction, Complex } from '@/types';

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [loading, setLoading] = useState(true);

  // 필터 상태
  const [selectedComplex, setSelectedComplex] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');

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
    const fetchTransactions = async () => {
      setLoading(true);
      try {
        const params: any = {
          limit: 50,
        };

        if (selectedComplex) params.complex_id = selectedComplex;
        if (startDate) params.start_date = startDate.replace(/-/g, '');
        if (endDate) params.end_date = endDate.replace(/-/g, '');
        if (minPrice) params.min_price = parseInt(minPrice) * 10000;
        if (maxPrice) params.max_price = parseInt(maxPrice) * 10000;

        const data = await transactionAPI.search(params);
        setTransactions(data);
      } catch (error) {
        console.error('실거래가 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [selectedComplex, startDate, endDate, minPrice, maxPrice]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900">실거래가 조회</h1>
        <p className="text-gray-600 mt-2">아파트 실거래가 정보를 확인하세요</p>
      </div>

      {/* 필터 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">검색 조건</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
            <label className="block text-sm font-medium text-gray-700 mb-2">시작일</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">종료일</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">최소 가격(억)</label>
            <input
              type="number"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              placeholder="예: 10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">최대 가격(억)</label>
            <input
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              placeholder="예: 15"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* 결과 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            실거래가 내역 {loading ? '...' : `(${transactions.length}건)`}
          </h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-600">로딩 중...</div>
        ) : transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-600">실거래가 정보가 없습니다</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    거래일
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    면적
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    층
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    거래가
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.trade_date?.replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {transaction.area}㎡
                      {transaction.exclusive_area && ` (전용 ${transaction.exclusive_area}㎡)`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {transaction.floor}층
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-purple-600">
                      {transaction.formatted_price}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
