'use client';

import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PriceTrendData {
  month: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  count: number;
}

interface PriceTrendChartProps {
  complexId: string;
  months?: number;
}

export default function PriceTrendChart({ complexId, months = 6 }: PriceTrendChartProps) {
  const [trendData, setTrendData] = useState<PriceTrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTrendData();
  }, [complexId, months]);

  const fetchTrendData = async () => {
    try {
      setLoading(true);
      setError(null);

      const apiUrl = typeof window === 'undefined'
        ? (process.env.NEXT_PUBLIC_API_URL || 'http://api:8000')
        : (process.env.NEXT_PUBLIC_API_URL || `http://${window.location.hostname}:8000`);

      const response = await fetch(
        `${apiUrl}/api/transactions/stats/price-trend?complex_id=${complexId}&months=${months}`
      );

      if (!response.ok) {
        throw new Error('가격 추이 데이터를 불러오는데 실패했습니다.');
      }

      const data = await response.json();
      setTrendData(data.trend || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">차트 로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  if (!trendData || trendData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">실거래 데이터가 없습니다.</div>
      </div>
    );
  }

  // 데이터를 시간순 정렬 (과거 → 현재)
  const sortedData = [...trendData].sort((a, b) => a.month.localeCompare(b.month));

  // 월 라벨 포맷 (YYYYMM → YYYY년 MM월)
  const labels = sortedData.map(d => {
    const year = d.month.substring(0, 4);
    const month = d.month.substring(4, 6);
    return `${year}.${month}`;
  });

  // 가격을 억원 단위로 변환
  const toEok = (price: number) => price / 10000;

  const chartData = {
    labels,
    datasets: [
      {
        label: '평균가',
        data: sortedData.map(d => toEok(d.avg_price)),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.3,
        fill: true,
      },
      {
        label: '최고가',
        data: sortedData.map(d => toEok(d.max_price)),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        borderDash: [5, 5],
        tension: 0.3,
        fill: false,
      },
      {
        label: '최저가',
        data: sortedData.map(d => toEok(d.min_price)),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        borderDash: [5, 5],
        tension: 0.3,
        fill: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `실거래가 추이 (최근 ${months}개월)`,
        font: {
          size: 16,
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += context.parsed.y.toFixed(1) + '억';
            }
            return label;
          },
          afterBody: function(tooltipItems: any[]) {
            const index = tooltipItems[0].dataIndex;
            const count = sortedData[index].count;
            return `거래건수: ${count}건`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function(value: any) {
            return value.toFixed(1) + '억';
          }
        },
        title: {
          display: true,
          text: '거래가격 (억원)',
        },
      },
      x: {
        title: {
          display: true,
          text: '거래월',
        },
      },
    },
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="h-96">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
