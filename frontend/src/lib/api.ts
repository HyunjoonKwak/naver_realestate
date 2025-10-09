import axios from 'axios';
import type { Complex, Article, Transaction, ArticleChangeSummary, ArticleChangeList, TransactionSummary } from '@/types';

// 브라우저에서는 NEXT_PUBLIC_API_URL 사용 (개발: localhost:8000, 프로덕션: 상대경로)
// SSR에서는 컨테이너 내부 API 사용
const API_URL = typeof window === 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://api:8000')  // SSR: 컨테이너 내부
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');  // 브라우저: 환경변수 또는 localhost

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Complex API
export const complexAPI = {
  getAll: () => api.get<Complex[]>('/api/complexes'),
  getById: (id: number) => api.get<Complex>(`/api/complexes/${id}`),
  getDetail: (id: string) => api.get(`/api/complexes/${id}`),
  getStats: (id: string) => api.get(`/api/complexes/${id}/stats`),
  delete: (id: string) => api.delete(`/api/complexes/${id}`),
  getList: (offset: number, limit: number) => api.get<Complex[]>(`/api/complexes/?offset=${offset}&limit=${limit}`),
  updateAddress: (id: string, address: string) => api.patch(`/api/complexes/${id}/address`, { address }),
  collectAddress: (id: string) => api.post(`/api/complexes/${id}/collect-address`),
};

// Article API
export const articleAPI = {
  getAll: (params?: any) => api.get<Article[]>('/api/articles', { params }),
  getById: (id: number) => api.get<Article>(`/api/articles/${id}`),
  getByComplex: (complexId: number) => api.get<Article[]>(`/api/articles/complex/${complexId}`),
  getChangeSummary: (complexId: string, hours: number = 24) =>
    api.get<ArticleChangeSummary>(`/api/articles/changes/${complexId}/summary?hours=${hours}`),
  getChangeList: (complexId: string, hours: number = 24, limit?: number) =>
    api.get<ArticleChangeList>(`/api/articles/changes/${complexId}/list?hours=${hours}${limit ? `&limit=${limit}` : ''}`),
};

// Transaction API
export const transactionAPI = {
  getAll: (params?: any) => api.get<Transaction[]>('/api/transactions', { params }),
  getById: (id: number) => api.get<Transaction>(`/api/transactions/${id}`),
  getByComplex: (complexId: number) => api.get<Transaction[]>(`/api/transactions/complex/${complexId}`),
  getPriceTrend: (complexId: string, months: number) => api.get(`/api/transactions/complex/${complexId}/price-trend?months=${months}`),
  getAreaSummary: (complexId: string, months: number = 6) =>
    api.get<TransactionSummary>(`/api/transactions/stats/area-summary/${complexId}?months=${months}`),
  search: (params?: any) => api.get<Transaction[]>('/api/transactions/', { params }),
  fetchFromMOLIT: (complexId: string, months: number = 6) =>
    api.post(`/api/transactions/fetch/${complexId}?months=${months}`),
  fetchAllFromMOLIT: (months: number = 6) =>
    api.post(`/api/transactions/fetch-all?months=${months}`),
  getOverview: () => api.get('/api/transactions/stats/overview'),
};

// Scraper API
export const scraperAPI = {
  refresh: (complexId: string) => {
    const url = `/api/scraper/refresh/${complexId}`;
    console.log('[API] scraperAPI.refresh called with URL:', url);
    return api.post(url);
  },
  getRefreshStatus: (complexId: string) => api.get(`/api/scraper/refresh/${complexId}/status`),
  getCrawlStatus: (complexId: string) => api.get(`/api/scraper/crawl/${complexId}/status`),
};

// Scheduler API
export const schedulerAPI = {
  getSchedule: () => api.get('/api/scheduler/schedule'),
  getStatus: () => api.get('/api/scheduler/status'),
  createSchedule: (data: {
    name: string;
    task: string;
    hour: number;
    minute: number;
    day_of_week?: string;
    description?: string;
  }) => api.post('/api/scheduler/schedule', data),
  updateSchedule: (name: string, data: {
    task?: string;
    hour?: number;
    minute?: number;
    day_of_week?: string;
    enabled?: boolean;
  }) => api.put(`/api/scheduler/schedule/${name}`, data),
  deleteSchedule: (name: string) => api.delete(`/api/scheduler/schedule/${name}`),
  triggerAll: () => api.post('/api/scheduler/trigger/all'),
  triggerComplex: (complexId: string) => api.post(`/api/scheduler/trigger/${complexId}`),
  getTaskStatus: (taskId: string) => api.get(`/api/scheduler/task/${taskId}`),
};

export default api;
