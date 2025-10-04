'use client';

import { useEffect, useState } from 'react';
import { complexAPI } from '@/lib/api';
import type { Complex } from '@/types';

export default function ComplexesPage() {
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchComplexes = async () => {
      try {
        const data = await complexAPI.getList();
        setComplexes(data);
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchComplexes();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-xl text-gray-600">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900">단지 목록</h1>
        <p className="text-gray-600 mt-2">등록된 아파트 단지 목록입니다</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {complexes.map((complex) => (
          <a
            key={complex.id}
            href={`/complexes/${complex.complex_id}`}
            className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-3">{complex.complex_name}</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>유형</span>
                <span className="font-medium">{complex.complex_type}</span>
              </div>
              <div className="flex justify-between">
                <span>세대수</span>
                <span className="font-medium">{complex.total_households}세대</span>
              </div>
              <div className="flex justify-between">
                <span>동수</span>
                <span className="font-medium">{complex.total_dongs}개동</span>
              </div>
              <div className="flex justify-between">
                <span>면적</span>
                <span className="font-medium">{complex.min_area}㎡ ~ {complex.max_area}㎡</span>
              </div>
              {complex.min_price && complex.max_price && (
                <div className="flex justify-between pt-2 border-t">
                  <span>매매가</span>
                  <span className="font-semibold text-blue-600">
                    {(complex.min_price / 10000).toFixed(1)}억 ~ {(complex.max_price / 10000).toFixed(1)}억
                  </span>
                </div>
              )}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
