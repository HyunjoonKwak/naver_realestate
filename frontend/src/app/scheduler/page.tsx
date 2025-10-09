'use client';

import { useState, useEffect } from 'react';
import { schedulerAPI } from '@/lib/api';
import axios from 'axios';

interface CrawlJob {
  id: number;
  job_id: string;
  job_type: string;
  complex_id?: string;
  complex_name?: string;
  status: string;
  started_at: string;
  finished_at?: string;
  duration_seconds?: number;
  articles_collected?: number;
  articles_new?: number;
  articles_updated?: number;
  error_message?: string;
}

interface ArticleSnapshot {
  snapshot_id: number;
  article_no: string;
  article_name: string;
  trade_type: string;
  price: number;
  area: number;
  floor?: number;
  direction?: string;
  is_active: boolean;
  captured_at: string;
}

interface ArticleChange {
  change_id: number;
  article_no: string;
  change_type: string;
  article_name: string;
  trade_type: string;
  old_price?: number;
  new_price?: number;
  price_diff?: number;
  detected_at: string;
}

interface JobDetail {
  job: CrawlJob & {
    error_traceback?: string;
    celery_task_id?: string;
    created_at?: string;
  };
  snapshots: {
    count: number;
    data: ArticleSnapshot[];
  };
  changes: {
    count: number;
    data: ArticleChange[];
  };
}

interface CrawlStats {
  total_jobs: number;
  success_count: number;
  failed_count: number;
  success_rate: number;
  avg_duration_seconds?: number;
  recent_24h: {
    total: number;
    success: number;
    failed: number;
  };
}

interface WorkerStatus {
  celery_worker_active: boolean;
  celery_beat_active: boolean;
  beat_schedule?: string[];
  workers?: {
    active: boolean;
    count: number;
  };
  beat?: {
    active: boolean;
    lock_ttl?: number;
  };
}

export default function SchedulerPage() {
  // API Base URL - 브라우저에서는 현재 호스트의 8000 포트 사용
  const [apiBaseUrl] = useState(() => {
    if (typeof window === 'undefined') {
      return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    }
    return process.env.NEXT_PUBLIC_API_URL || `http://${window.location.hostname}:8000`;
  });

  const [activeTab, setActiveTab] = useState<'monitor' | 'schedule'>('monitor');

  // 모니터링 상태
  const [jobs, setJobs] = useState<CrawlJob[]>([]);
  const [stats, setStats] = useState<CrawlStats | null>(null);
  const [workerStatus, setWorkerStatus] = useState<WorkerStatus | null>(null);
  const [runningJobs, setRunningJobs] = useState<CrawlJob[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // 스케줄 관리 상태
  const [schedules, setSchedules] = useState<Record<string, any>>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [loading, setLoading] = useState(false);
  const [triggeringAll, setTriggeringAll] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [hasInitialData, setHasInitialData] = useState(false);

  // 작업 상세 모달 상태
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedJobDetail, setSelectedJobDetail] = useState<JobDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // 폼 상태
  const [formData, setFormData] = useState({
    name: '',
    task: 'app.tasks.scheduler.crawl_all_complexes',
    hour: 6,
    minute: 0,
    day_of_week: '*',
    description: '',
  });

  // 편집 폼 상태
  const [editFormData, setEditFormData] = useState({
    name: '',
    task: 'app.tasks.scheduler.crawl_all_complexes',
    hour: 6,
    minute: 0,
    day_of_week: '*',
  });

  // Initial load only once
  useEffect(() => {
    if (activeTab === 'monitor') {
      fetchMonitoringData();
    } else {
      loadSchedules();
      loadStatus();
    }
  }, []);

  // Tab change (skip initial load)
  useEffect(() => {
    if (hasInitialData) {
      if (activeTab === 'monitor') {
        fetchMonitoringData();
      } else {
        loadSchedules();
        loadStatus();
      }
    }
  }, [activeTab]);

  // Auto-refresh for monitoring tab only (10 seconds)
  useEffect(() => {
    if (activeTab === 'monitor' && hasInitialData) {
      const interval = setInterval(() => {
        fetchMonitoringData(true); // silent refresh
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab, hasInitialData]);

  // Filter changes for monitoring tab
  useEffect(() => {
    if (activeTab === 'monitor' && hasInitialData) {
      fetchMonitoringData(true);
    }
  }, [filterStatus]);

  const fetchMonitoringData = async (silent: boolean = false) => {
    if (!silent) setLoading(true);

    try {
      // Fast API calls first
      const [jobsRes, statsRes, runningRes] = await Promise.all([
        axios.get(`${apiBaseUrl}/api/scheduler/jobs`, {
          params: filterStatus !== 'all' ? { status: filterStatus } : {},
          timeout: 3000
        }),
        axios.get(`${apiBaseUrl}/api/scheduler/stats`, { timeout: 3000 }),
        axios.get(`${apiBaseUrl}/api/scheduler/jobs/running/current`, { timeout: 3000 })
      ]);

      setJobs(jobsRes.data.jobs || []);
      setStats(statsRes.data);
      setRunningJobs(runningRes.data.jobs || []);
      setLastUpdate(new Date());
      if (!hasInitialData) setHasInitialData(true);

      // Fetch status separately (slower, non-blocking)
      if (!silent || !workerStatus) {
        axios.get(`${apiBaseUrl}/api/scheduler/status`, { timeout: 3000 })
          .then(res => setWorkerStatus(res.data))
          .catch(err => console.error('Status fetch failed:', err));
      }
    } catch (error) {
      if (!silent) {
        console.error('Failed to fetch monitoring data:', error);
      }
      if (!hasInitialData) setHasInitialData(true);
    } finally {
      setLoading(false);
    }
  };

  const loadSchedules = async () => {
    try {
      const response = await schedulerAPI.getSchedule();
      setSchedules(response.data.schedule);
      if (!hasInitialData) setHasInitialData(true);
    } catch (error) {
      console.error('스케줄 로드 실패:', error);
      showMessage('error', '스케줄을 불러오는데 실패했습니다.');
      if (!hasInitialData) setHasInitialData(true);
    }
  };

  const loadStatus = async () => {
    try {
      const response = await schedulerAPI.getStatus();
      setWorkerStatus(response.data);
    } catch (error) {
      console.error('상태 로드 실패:', error);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const restartBeat = async () => {
    if (!confirm('Celery Beat를 재시작하시겠습니까?\n\n기존 프로세스를 종료하고 새로운 프로세스를 시작합니다.')) return;

    try {
      const response = await axios.post(`${apiBaseUrl}/api/scheduler/beat/restart`);
      showMessage('success', response.data.message || '✅ Celery Beat가 재시작되었습니다!');

      // 5초 후 상태 갱신
      setTimeout(() => {
        if (activeTab === 'schedule') loadStatus();
      }, 5000);
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || 'Beat 재시작에 실패했습니다.');
    }
  };

  const triggerAllCrawling = async () => {
    if (!confirm('전체 단지 크롤링을 시작하시겠습니까?')) return;

    setTriggeringAll(true);
    try {
      const response = await axios.post(`${apiBaseUrl}/api/scheduler/trigger/all`);
      showMessage('success', `크롤링이 시작되었습니다! Job ID: ${response.data.job_id}`);
      if (activeTab === 'monitor') fetchMonitoringData();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || error.message);
    } finally {
      setTriggeringAll(false);
    }
  };

  const triggerSingleCrawl = async (complexId: string, complexName: string) => {
    if (!confirm(`${complexName} 크롤링을 시작하시겠습니까?`)) return;

    try {
      const response = await axios.post(`${apiBaseUrl}/api/scheduler/trigger/${complexId}`);
      showMessage('success', `크롤링이 시작되었습니다! Job ID: ${response.data.job_id}`);
      if (activeTab === 'monitor') fetchMonitoringData();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || error.message);
    }
  };

  const handleDeleteJob = async (jobId: string, jobName: string) => {
    if (!confirm(`'${jobName}' 작업을 삭제하시겠습니까?`)) return;

    try {
      await axios.delete(`${apiBaseUrl}/api/scheduler/jobs/${jobId}`);
      showMessage('success', '작업이 삭제되었습니다.');
      fetchMonitoringData();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || '작업 삭제에 실패했습니다.');
    }
  };

  const handleViewJobDetail = async (jobId: string) => {
    setLoadingDetail(true);
    setShowDetailModal(true);

    try {
      const response = await axios.get(`${apiBaseUrl}/api/scheduler/jobs/${jobId}/detail`);
      setSelectedJobDetail(response.data);
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || '작업 상세 조회에 실패했습니다.');
      setShowDetailModal(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await schedulerAPI.createSchedule(formData);
      showMessage('success', '✅ 스케줄이 생성되었습니다! 5초 이내 자동 반영됩니다.');
      setShowCreateModal(false);
      loadSchedules();
      setFormData({
        name: '',
        task: 'app.tasks.scheduler.crawl_all_complexes',
        hour: 6,
        minute: 0,
        day_of_week: '*',
        description: '',
      });
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || '스케줄 생성에 실패했습니다.');
    }
  };

  const handleOpenEditModal = (scheduleName: string, config: any) => {
    const parsedSchedule = parseCronSchedule(config.schedule);
    setEditFormData({
      name: scheduleName,
      task: config.task,
      hour: parsedSchedule.hour,
      minute: parsedSchedule.minute,
      day_of_week: parsedSchedule.day_of_week,
    });
    setShowEditModal(true);
  };

  const handleUpdateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await schedulerAPI.updateSchedule(editFormData.name, {
        task: editFormData.task,
        hour: editFormData.hour,
        minute: editFormData.minute,
        day_of_week: editFormData.day_of_week,
      });
      showMessage('success', '✅ 스케줄이 수정되었습니다! 5초 이내 자동 반영됩니다.');
      setShowEditModal(false);
      loadSchedules();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || '스케줄 수정에 실패했습니다.');
    }
  };

  const handleDeleteSchedule = async (scheduleName: string) => {
    if (!confirm(`'${scheduleName}' 스케줄을 삭제하시겠습니까?`)) return;

    try {
      await schedulerAPI.deleteSchedule(scheduleName);
      showMessage('success', '✅ 스케줄이 삭제되었습니다! 5초 이내 자동 반영됩니다.');
      loadSchedules();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || '스케줄 삭제에 실패했습니다.');
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}초`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}분 ${secs}초`;
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('ko-KR');
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      success: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      pending: 'bg-gray-100 text-gray-800',
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold ${colors[status] || colors.pending}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  const getElapsedTime = (startedAt: string) => {
    const start = new Date(startedAt);
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - start.getTime()) / 1000);
    return formatDuration(Math.abs(diffSeconds));
  };

  const parseCronSchedule = (cronStr: string) => {
    // Cron format: minute hour day month day_of_week
    const match = cronStr.match(/(\d+)\s+(\d+)\s+[\d\*]+\s+[\d\*,]+\s+([\d\*]+)/);
    if (match) {
      return {
        minute: parseInt(match[1]),
        hour: parseInt(match[2]),
        day_of_week: match[3],
      };
    }
    // Fallback for simpler format: minute hour * * day_of_week
    const simpleMatch = cronStr.match(/(\d+)\s+(\d+)\s+\*\s+\*\s+([\d\*]+)/);
    if (simpleMatch) {
      return {
        minute: parseInt(simpleMatch[1]),
        hour: parseInt(simpleMatch[2]),
        day_of_week: simpleMatch[3],
      };
    }
    return { minute: 0, hour: 0, day_of_week: '*' };
  };

  const getDayOfWeekText = (dow: string) => {
    if (dow === '*') return '매일';
    // Cron day_of_week: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
    const days = ['일', '월', '화', '수', '목', '금', '토'];
    return days[parseInt(dow)] || dow;
  };

  const getTaskDisplayName = (task: string) => {
    if (task.includes('crawl_all_complexes')) return '전체 단지 크롤링';
    if (task.includes('cleanup_old_snapshots')) return '오래된 스냅샷 정리';
    if (task.includes('send_weekly_briefing')) return '주간 브리핑 발송';
    return task;
  };

  // Show skeleton UI while loading initial data
  if (!hasInitialData) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6 flex justify-between items-center">
            <div className="h-9 w-48 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-10 w-40 bg-gray-200 rounded animate-pulse"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse mb-2"></div>
                <div className="h-8 w-16 bg-gray-200 rounded animate-pulse"></div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse mb-2"></div>
                <div className="h-8 w-16 bg-gray-200 rounded animate-pulse"></div>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-4"></div>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <h1 className="text-3xl font-bold text-gray-900">크롤링 스케줄러</h1>
            <button
              onClick={triggerAllCrawling}
              disabled={triggeringAll || !workerStatus?.workers?.active}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {triggeringAll ? '실행 중...' : '🚀 전체 크롤링 실행'}
            </button>
          </div>
          {activeTab === 'monitor' && lastUpdate && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>마지막 업데이트: {lastUpdate.toLocaleTimeString('ko-KR')}</span>
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span>10초마다 자동 새로고침</span>
            </div>
          )}
        </div>

        {/* 메시지 */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
          </div>
        )}

        {/* 탭 */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('monitor')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'monitor'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 모니터링
            </button>
            <button
              onClick={() => setActiveTab('schedule')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'schedule'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ⚙️ 스케줄 관리
            </button>
          </nav>
        </div>

        {/* Worker Status (공통) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Celery Worker</p>
                <p className="text-2xl font-bold mt-1">
                  {workerStatus?.workers?.active ? (
                    <span className="text-green-600">활성</span>
                  ) : (
                    <span className="text-red-600">비활성</span>
                  )}
                </p>
              </div>
              <div className={`w-4 h-4 rounded-full ${workerStatus?.workers?.active ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-sm text-gray-600">Celery Beat</p>
                <p className="text-2xl font-bold mt-1">
                  {workerStatus?.beat?.active ? (
                    <span className="text-green-600">활성</span>
                  ) : (
                    <span className="text-red-600">비활성</span>
                  )}
                </p>
                {workerStatus?.beat?.lock_ttl && (
                  <p className="text-xs text-gray-500 mt-1">
                    Lock TTL: {Math.floor(workerStatus.beat.lock_ttl / 60)}분
                  </p>
                )}
              </div>
              <div className={`w-4 h-4 rounded-full ${workerStatus?.beat?.active ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            </div>
            {!workerStatus?.beat?.active && (
              <button
                onClick={restartBeat}
                className="w-full mt-3 px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                🔄 재활성화
              </button>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600">등록된 스케줄</p>
            <p className="text-2xl font-bold mt-1">{workerStatus?.beat_schedule?.length || 0}개</p>
          </div>
        </div>

        {/* 모니터링 탭 */}
        {activeTab === 'monitor' && (
          <>
            {/* Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">총 작업 수</p>
                <p className="text-2xl font-bold mt-1">{stats?.total_jobs || 0}</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">성공률</p>
                <p className="text-2xl font-bold mt-1 text-green-600">
                  {stats?.success_rate ? `${stats.success_rate}%` : '0%'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {stats?.success_count || 0}건 성공 / {stats?.failed_count || 0}건 실패
                </p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">평균 소요시간</p>
                <p className="text-2xl font-bold mt-1">{formatDuration(stats?.avg_duration_seconds)}</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-600">최근 24시간</p>
                <p className="text-2xl font-bold mt-1">{stats?.recent_24h?.total || 0}건</p>
                <p className="text-xs text-gray-500 mt-1">
                  성공 {stats?.recent_24h?.success || 0} / 실패 {stats?.recent_24h?.failed || 0}
                </p>
              </div>
            </div>

            {/* Running Jobs */}
            {runningJobs.length > 0 && (
              <div className="bg-white rounded-lg shadow mb-6 p-6">
                <h2 className="text-xl font-bold mb-4">🔄 실행 중인 작업</h2>
                <div className="space-y-3">
                  {runningJobs.map((job) => (
                    <div key={job.job_id} className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                      <div>
                        <p className="font-semibold">{job.complex_name || '전체 단지'}</p>
                        <p className="text-sm text-gray-600">Job ID: {job.job_id}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-blue-600">{getElapsedTime(job.started_at)}</p>
                        <p className="text-xs text-gray-600">{formatDateTime(job.started_at)} 시작</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Job History */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">작업 이력</h2>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-lg"
                >
                  <option value="all">전체</option>
                  <option value="success">성공</option>
                  <option value="failed">실패</option>
                  <option value="running">실행중</option>
                </select>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">단지명</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">작업 유형</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">시작 시각</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">소요 시간</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">수집 결과</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">액션</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {jobs.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                          작업 이력이 없습니다
                        </td>
                      </tr>
                    ) : (
                      jobs.map((job) => (
                        <tr key={job.job_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">{getStatusBadge(job.status)}</td>
                          <td className="px-4 py-3">
                            <div className="font-medium">{job.complex_name || '-'}</div>
                            {job.complex_id && (
                              <div className="text-xs text-gray-500">{job.complex_id}</div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm capitalize">{job.job_type}</span>
                          </td>
                          <td className="px-4 py-3 text-sm">{formatDateTime(job.started_at)}</td>
                          <td className="px-4 py-3 text-sm">{formatDuration(job.duration_seconds)}</td>
                          <td className="px-4 py-3 text-sm">
                            {job.status === 'success' ? (
                              <div>
                                <div>수집: {job.articles_collected || 0}건</div>
                                <div className="text-xs text-gray-500">
                                  신규 {job.articles_new || 0} / 업데이트 {job.articles_updated || 0}
                                </div>
                              </div>
                            ) : job.status === 'failed' ? (
                              <span className="text-red-600 text-xs">{job.error_message?.substring(0, 50)}</span>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleViewJobDetail(job.job_id)}
                                className="text-blue-600 hover:text-blue-800 text-sm"
                              >
                                상세
                              </button>
                              {job.complex_id && job.status === 'failed' && (
                                <button
                                  onClick={() => triggerSingleCrawl(job.complex_id!, job.complex_name!)}
                                  className="text-green-600 hover:text-green-800 text-sm"
                                >
                                  재실행
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteJob(job.job_id, job.complex_name || job.job_id)}
                                className="text-red-600 hover:text-red-800 text-sm"
                              >
                                삭제
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {jobs.length > 0 && (
                <div className="mt-4 text-sm text-gray-500 text-center">
                  총 {jobs.length}건의 작업 이력
                </div>
              )}
            </div>
          </>
        )}

        {/* 스케줄 관리 탭 */}
        {activeTab === 'schedule' && (
          <>
            {/* 액션 버튼 */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                + 스케줄 추가
              </button>
              <button
                onClick={() => {
                  loadSchedules();
                  loadStatus();
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                ↻ 새로고침
              </button>
            </div>

            {/* 스케줄 목록 */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      스케줄 이름
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      실행 시간
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      반복
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(schedules).map(([name, config]) => {
                    const parsedSchedule = parseCronSchedule(config.schedule);

                    return (
                      <tr key={name} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{getTaskDisplayName(config.task)}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {String(parsedSchedule.hour).padStart(2, '0')}:{String(parsedSchedule.minute).padStart(2, '0')}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">
                            {getDayOfWeekText(parsedSchedule.day_of_week)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex gap-3 justify-end">
                            <button
                              onClick={() => handleOpenEditModal(name, config)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              수정
                            </button>
                            <button
                              onClick={() => handleDeleteSchedule(name)}
                              className="text-red-600 hover:text-red-900"
                            >
                              삭제
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {Object.keys(schedules).length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  등록된 스케줄이 없습니다.
                </div>
              )}
            </div>
          </>
        )}

        {/* 생성 모달 */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-bold mb-4">새 스케줄 추가</h2>
              <form onSubmit={handleCreateSchedule}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      스케줄 이름
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="예: crawl-all-complexes-noon"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      작업 유형
                    </label>
                    <select
                      value={formData.task}
                      onChange={(e) => setFormData({ ...formData, task: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="app.tasks.scheduler.crawl_all_complexes">전체 단지 크롤링</option>
                      <option value="app.tasks.scheduler.cleanup_old_snapshots">오래된 스냅샷 정리</option>
                      <option value="app.tasks.briefing_tasks.send_weekly_briefing">주간 브리핑 발송</option>
                      <option value="app.tasks.briefing_tasks.send_custom_briefing">커스텀 브리핑 발송</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        시 (0-23)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="23"
                        required
                        value={formData.hour}
                        onChange={(e) => setFormData({ ...formData, hour: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        분 (0-59)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="59"
                        required
                        value={formData.minute}
                        onChange={(e) => setFormData({ ...formData, minute: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      반복 주기
                    </label>
                    <select
                      value={formData.day_of_week}
                      onChange={(e) => setFormData({ ...formData, day_of_week: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="*">매일</option>
                      <option value="1">매주 월요일</option>
                      <option value="2">매주 화요일</option>
                      <option value="3">매주 수요일</option>
                      <option value="4">매주 목요일</option>
                      <option value="5">매주 금요일</option>
                      <option value="6">매주 토요일</option>
                      <option value="0">매주 일요일</option>
                      <option value="QUARTERLY_1">분기별 (1월, 4월, 7월, 10월 1일)</option>
                      <option value="QUARTERLY_15">분기별 (1월, 4월, 7월, 10월 15일)</option>
                      <option value="MONTHLY_1">매월 1일</option>
                      <option value="MONTHLY_15">매월 15일</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      설명 (선택)
                    </label>
                    <input
                      type="text"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="스케줄 설명"
                    />
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    생성
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    취소
                  </button>
                </div>
              </form>

              <div className="mt-4 p-3 bg-green-50 text-green-800 text-sm rounded-lg">
                ✅ RedBeat 사용: 스케줄 변경사항은 5초 이내 자동 반영됩니다 (재시작 불필요)
              </div>
            </div>
          </div>
        )}

        {/* 편집 모달 */}
        {showEditModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-bold mb-4">스케줄 수정</h2>
              <form onSubmit={handleUpdateSchedule}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      스케줄 이름
                    </label>
                    <input
                      type="text"
                      disabled
                      value={editFormData.name}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      작업 유형
                    </label>
                    <select
                      value={editFormData.task}
                      onChange={(e) => setEditFormData({ ...editFormData, task: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="app.tasks.scheduler.crawl_all_complexes">전체 단지 크롤링</option>
                      <option value="app.tasks.scheduler.cleanup_old_snapshots">오래된 스냅샷 정리</option>
                      <option value="app.tasks.briefing_tasks.send_weekly_briefing">주간 브리핑 발송</option>
                      <option value="app.tasks.briefing_tasks.send_custom_briefing">커스텀 브리핑 발송</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        시 (0-23)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="23"
                        required
                        value={editFormData.hour}
                        onChange={(e) => setEditFormData({ ...editFormData, hour: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        분 (0-59)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="59"
                        required
                        value={editFormData.minute}
                        onChange={(e) => setEditFormData({ ...editFormData, minute: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      반복 주기
                    </label>
                    <select
                      value={editFormData.day_of_week}
                      onChange={(e) => setEditFormData({ ...editFormData, day_of_week: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="*">매일</option>
                      <option value="1">매주 월요일</option>
                      <option value="2">매주 화요일</option>
                      <option value="3">매주 수요일</option>
                      <option value="4">매주 목요일</option>
                      <option value="5">매주 금요일</option>
                      <option value="6">매주 토요일</option>
                      <option value="0">매주 일요일</option>
                      <option value="QUARTERLY_1">분기별 (1월, 4월, 7월, 10월 15일)</option>
                      <option value="QUARTERLY_15">분기별 (1월, 4월, 7월, 10월 15일)</option>
                      <option value="MONTHLY_1">매월 1일</option>
                      <option value="MONTHLY_15">매월 15일</option>
                    </select>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    수정
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    취소
                  </button>
                </div>
              </form>

              <div className="mt-4 p-3 bg-green-50 text-green-800 text-sm rounded-lg">
                ✅ RedBeat 사용: 스케줄 변경사항은 5초 이내 자동 반영됩니다 (재시작 불필요)
              </div>
            </div>
          </div>
        )}

        {/* 작업 상세 모달 */}
        {showDetailModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-bold">작업 상세 정보</h3>
                  <button
                    onClick={() => {
                      setShowDetailModal(false);
                      setSelectedJobDetail(null);
                    }}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>

                {loadingDetail ? (
                  <div className="text-center py-8">로딩 중...</div>
                ) : selectedJobDetail ? (
                  <div className="space-y-6">
                    {/* 작업 기본 정보 */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-bold mb-3">기본 정보</h4>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div><span className="font-medium">작업 ID:</span> {selectedJobDetail.job.job_id}</div>
                        <div><span className="font-medium">작업 유형:</span> {selectedJobDetail.job.job_type}</div>
                        <div><span className="font-medium">상태:</span> {getStatusBadge(selectedJobDetail.job.status)}</div>
                        <div><span className="font-medium">단지명:</span> {selectedJobDetail.job.complex_name || '-'}</div>
                        <div><span className="font-medium">시작 시각:</span> {formatDateTime(selectedJobDetail.job.started_at)}</div>
                        <div><span className="font-medium">완료 시각:</span> {selectedJobDetail.job.finished_at ? formatDateTime(selectedJobDetail.job.finished_at) : '-'}</div>
                        <div><span className="font-medium">소요 시간:</span> {formatDuration(selectedJobDetail.job.duration_seconds)}</div>
                        <div><span className="font-medium">수집 매물:</span> {selectedJobDetail.job.articles_collected || 0}건</div>
                        <div><span className="font-medium">신규:</span> {selectedJobDetail.job.articles_new || 0}건</div>
                        <div><span className="font-medium">업데이트:</span> {selectedJobDetail.job.articles_updated || 0}건</div>
                      </div>
                      {selectedJobDetail.job.error_message && (
                        <div className="mt-3">
                          <span className="font-medium text-red-600">오류 메시지:</span>
                          <p className="text-red-600 text-sm mt-1">{selectedJobDetail.job.error_message}</p>
                        </div>
                      )}
                    </div>

                    {/* 변경사항 */}
                    {selectedJobDetail.changes.count > 0 && (
                      <div>
                        <h4 className="font-bold mb-3">가격 변경 내역 ({selectedJobDetail.changes.count}건)</h4>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200 text-sm">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">유형</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">매물</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">거래유형</th>
                                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">기존가격</th>
                                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">변경가격</th>
                                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">변동</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">감지시각</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {selectedJobDetail.changes.data.map((change) => (
                                <tr key={change.change_id} className="hover:bg-gray-50">
                                  <td className="px-3 py-2">
                                    <span className={`px-2 py-1 text-xs rounded ${
                                      change.change_type === 'NEW' ? 'bg-green-100 text-green-800' :
                                      change.change_type === 'REMOVED' ? 'bg-red-100 text-red-800' :
                                      change.change_type === 'PRICE_UP' ? 'bg-orange-100 text-orange-800' :
                                      'bg-blue-100 text-blue-800'
                                    }`}>
                                      {change.change_type}
                                    </span>
                                  </td>
                                  <td className="px-3 py-2">{change.article_name}</td>
                                  <td className="px-3 py-2">{change.trade_type}</td>
                                  <td className="px-3 py-2 text-right">{change.old_price ? `${change.old_price.toLocaleString()}만` : '-'}</td>
                                  <td className="px-3 py-2 text-right">{change.new_price ? `${change.new_price.toLocaleString()}만` : '-'}</td>
                                  <td className={`px-3 py-2 text-right font-medium ${
                                    change.price_diff && change.price_diff > 0 ? 'text-red-600' :
                                    change.price_diff && change.price_diff < 0 ? 'text-blue-600' : ''
                                  }`}>
                                    {change.price_diff ? `${change.price_diff > 0 ? '+' : ''}${change.price_diff.toLocaleString()}만` : '-'}
                                  </td>
                                  <td className="px-3 py-2">{formatDateTime(change.detected_at)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* 스냅샷 */}
                    {selectedJobDetail.snapshots.count > 0 && (
                      <div>
                        <h4 className="font-bold mb-3">매물 스냅샷 ({selectedJobDetail.snapshots.count}건)</h4>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200 text-sm">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">매물명</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">거래유형</th>
                                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">가격</th>
                                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">면적</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">층</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">방향</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">수집시각</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {selectedJobDetail.snapshots.data.slice(0, 50).map((snapshot) => (
                                <tr key={snapshot.snapshot_id} className="hover:bg-gray-50">
                                  <td className="px-3 py-2">{snapshot.article_name}</td>
                                  <td className="px-3 py-2">{snapshot.trade_type}</td>
                                  <td className="px-3 py-2 text-right">{snapshot.price.toLocaleString()}만</td>
                                  <td className="px-3 py-2 text-right">{snapshot.area}㎡</td>
                                  <td className="px-3 py-2">{snapshot.floor || '-'}</td>
                                  <td className="px-3 py-2">{snapshot.direction || '-'}</td>
                                  <td className="px-3 py-2">
                                    <span className={`px-2 py-1 text-xs rounded ${
                                      snapshot.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                    }`}>
                                      {snapshot.is_active ? '활성' : '비활성'}
                                    </span>
                                  </td>
                                  <td className="px-3 py-2">{formatDateTime(snapshot.captured_at)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {selectedJobDetail.snapshots.count > 50 && (
                            <p className="text-sm text-gray-500 mt-2 text-center">
                              상위 50개만 표시됩니다 (전체 {selectedJobDetail.snapshots.count}건)
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {selectedJobDetail.snapshots.count === 0 && selectedJobDetail.changes.count === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        이 작업의 스냅샷 및 변경사항이 없습니다.
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
