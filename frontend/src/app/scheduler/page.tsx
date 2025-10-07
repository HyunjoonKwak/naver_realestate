'use client';

import { useState, useEffect } from 'react';
import { schedulerAPI } from '@/lib/api';

interface Schedule {
  name: string;
  task: string;
  schedule: string;
  hour: number;
  minute: number;
  day_of_week: string;
}

interface SchedulerStatus {
  workers: {
    active: boolean;
    count: number;
  };
  beat_schedule: string[];
}

export default function SchedulerPage() {
  const [schedules, setSchedules] = useState<Record<string, any>>({});
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

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

  useEffect(() => {
    loadSchedules();
    loadStatus();
  }, []);

  const loadSchedules = async () => {
    try {
      const response = await schedulerAPI.getSchedule();
      setSchedules(response.data.schedule);
    } catch (error) {
      console.error('스케줄 로드 실패:', error);
      showMessage('error', '스케줄을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const response = await schedulerAPI.getStatus();
      setStatus(response.data);
    } catch (error) {
      console.error('상태 로드 실패:', error);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await schedulerAPI.createSchedule(formData);
      showMessage('success', '스케줄이 생성되었습니다. Celery Beat를 재시작해주세요.');
      setShowCreateModal(false);
      loadSchedules();
      // 폼 리셋
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
      showMessage('success', '스케줄이 수정되었습니다. Celery Beat를 재시작해주세요.');
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
      showMessage('success', '스케줄이 삭제되었습니다. Celery Beat를 재시작해주세요.');
      loadSchedules();
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || '스케줄 삭제에 실패했습니다.');
    }
  };

  const handleTriggerAll = async () => {
    if (!confirm('모든 단지 크롤링을 시작하시겠습니까?')) return;

    try {
      const response = await schedulerAPI.triggerAll();
      showMessage('success', `크롤링이 시작되었습니다. Task ID: ${response.data.task_id}`);
    } catch (error: any) {
      showMessage('error', error.response?.data?.detail || '크롤링 시작에 실패했습니다.');
    }
  };

  const parseCronSchedule = (cronStr: string) => {
    // <crontab: 0 6 * * * (m/h/dM/MY/d)> 형식 파싱
    const match = cronStr.match(/(\d+)\s+(\d+)\s+\*\s+\*\s+([\d\*]+)/);
    if (match) {
      return {
        minute: parseInt(match[1]),
        hour: parseInt(match[2]),
        day_of_week: match[3],
      };
    }
    return { minute: 0, hour: 0, day_of_week: '*' };
  };

  const getDayOfWeekText = (dow: string) => {
    if (dow === '*') return '매일';
    const days = ['월', '화', '수', '목', '금', '토', '일'];
    return days[parseInt(dow)] || dow;
  };

  const getTaskDisplayName = (task: string) => {
    if (task.includes('crawl_all_complexes')) return '전체 단지 크롤링';
    if (task.includes('cleanup_old_snapshots')) return '오래된 스냅샷 정리';
    return task;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">스케줄러 관리</h1>
          <p className="text-gray-600">자동 크롤링 스케줄을 관리합니다.</p>
        </div>

        {/* 메시지 */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
          </div>
        )}

        {/* 상태 카드 */}
        {status && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">시스템 상태</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600">Celery Worker</div>
                <div className={`text-lg font-semibold ${
                  status.workers.active ? 'text-green-600' : 'text-red-600'
                }`}>
                  {status.workers.active ? `✓ 실행 중 (${status.workers.count}개)` : '✗ 중지됨'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">등록된 스케줄</div>
                <div className="text-lg font-semibold text-gray-900">
                  {status.beat_schedule.length}개
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 액션 버튼 */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            + 스케줄 추가
          </button>
          <button
            onClick={handleTriggerAll}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            ▶ 전체 크롤링 실행
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
                      반복 요일
                    </label>
                    <select
                      value={formData.day_of_week}
                      onChange={(e) => setFormData({ ...formData, day_of_week: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="*">매일</option>
                      <option value="0">월요일</option>
                      <option value="1">화요일</option>
                      <option value="2">수요일</option>
                      <option value="3">목요일</option>
                      <option value="4">금요일</option>
                      <option value="5">토요일</option>
                      <option value="6">일요일</option>
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

              <div className="mt-4 p-3 bg-yellow-50 text-yellow-800 text-sm rounded-lg">
                ⚠️ 스케줄을 추가/수정/삭제한 후에는 Celery Beat를 재시작해야 변경사항이 적용됩니다.
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
                      반복 요일
                    </label>
                    <select
                      value={editFormData.day_of_week}
                      onChange={(e) => setEditFormData({ ...editFormData, day_of_week: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="*">매일</option>
                      <option value="0">월요일</option>
                      <option value="1">화요일</option>
                      <option value="2">수요일</option>
                      <option value="3">목요일</option>
                      <option value="4">금요일</option>
                      <option value="5">토요일</option>
                      <option value="6">일요일</option>
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

              <div className="mt-4 p-3 bg-yellow-50 text-yellow-800 text-sm rounded-lg">
                ⚠️ 스케줄을 수정한 후에는 Celery Beat를 재시작해야 변경사항이 적용됩니다.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
