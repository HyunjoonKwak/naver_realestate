'use client';

import { useEffect, useState } from 'react';
import { transactionAPI, complexAPI } from '@/lib/api';
import type { Transaction, Complex } from '@/types';

interface ComplexTransactionStats {
  complex_id: string;
  complex_name: string;
  transaction_count: number;
  latest_date: string;
  avg_price: number;
  min_price: number;
  max_price: number;
}

interface OverviewStats {
  total_transactions: number;
  recent_7days: number;
  complex_count: number;
  complexes: ComplexTransactionStats[];
}

export default function TransactionsPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchingAll, setFetchingAll] = useState(false);

  // 필터 상태
  const [selectedComplex, setSelectedComplex] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [overviewRes, complexesRes] = await Promise.all([
        transactionAPI.getOverview(),
        complexAPI.getAll()
      ]);
      setOverview(overviewRes.data);
      setComplexes(complexesRes.data);
    } catch (error) {
      console.error('데이터 로딩 실패:', error);
    } finally {
      setLoading(false);
    }
  };

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

        const response = await transactionAPI.search(params);
        setTransactions(response.data);
      } catch (error) {
        console.error('실거래가 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [selectedComplex, startDate, endDate, minPrice, maxPrice]);

  const handleFetchAll = async () => {
    if (!confirm('모든 단지의 실거래가를 국토부 API에서 조회합니다. (최근 6개월)\n시간이 다소 걸릴 수 있습니다. 진행하시겠습니까?')) {
      return;
    }

    setFetchingAll(true);
    try {
      const response = await transactionAPI.fetchAllFromMOLIT(6);
      alert(`실거래가 수집 완료\n성공: ${response.data.success_count}개 단지\n실패: ${response.data.fail_count}개 단지`);
      fetchData();
    } catch (error: any) {
      alert(`실거래가 수집 실패: ${error.response?.data?.detail || error.message}`);
    } finally {
      setFetchingAll(false);
    }
  };

  const formatPrice = (price: number) => {
    if (!price) return '-';
    const eok = Math.floor(price / 10000);
    const man = price % 10000;
    if (man === 0) return `${eok}억`;
    return `${eok}억 ${man.toLocaleString()}`;
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">실거래가 총괄</h1>
            <p className="text-gray-600 mt-2">국토부 실거래가 데이터 조회 및 분석</p>
          </div>
          <button
            onClick={handleFetchAll}
            disabled={fetchingAll}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              fetchingAll
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            {fetchingAll ? '수집 중...' : '🔄 전체 단지 실거래가 수집'}
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
            <div className="text-sm font-medium opacity-90">총 실거래 건수</div>
            <div className="text-4xl font-bold mt-2">{overview.total_transactions.toLocaleString()}</div>
            <div className="text-sm mt-1 opacity-75">전체 단지</div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
            <div className="text-sm font-medium opacity-90">최근 7일 거래</div>
            <div className="text-4xl font-bold mt-2">{overview.recent_7days.toLocaleString()}</div>
            <div className="text-sm mt-1 opacity-75">새로운 거래</div>
          </div>

          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
            <div className="text-sm font-medium opacity-90">데이터 보유 단지</div>
            <div className="text-4xl font-bold mt-2">{overview.complex_count}</div>
            <div className="text-sm mt-1 opacity-75">/ {complexes.length}개 전체</div>
          </div>
        </div>
      )}

      {/* 단지별 실거래가 현황 */}
      {overview && overview.complexes.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-xl font-semibold text-gray-900">단지별 실거래가 현황</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    단지명
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    거래 건수
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    평균 거래가
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    최저가
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    최고가
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    최근 거래일
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {overview.complexes.map((complex) => (
                  <tr key={complex.complex_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <a
                        href={`/complexes/${complex.complex_id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {complex.complex_name}
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {complex.transaction_count}건
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-purple-600">
                      {formatPrice(complex.avg_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatPrice(complex.min_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatPrice(complex.max_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {complex.latest_date?.replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 필터 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">상세 검색</h2>
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
          <div className="p-8 text-center">
            <div className="text-gray-600 mb-4">실거래가 정보가 없습니다</div>
            <p className="text-sm text-gray-500">
              상단의 "전체 단지 실거래가 수집" 버튼을 눌러 국토부 데이터를 가져오세요
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    단지명
                  </th>
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {transaction.complex_name || '-'}
                    </td>
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
