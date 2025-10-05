'use client';

import { useEffect, useState } from 'react';
import { complexAPI } from '@/lib/api';
import type { Complex } from '@/types';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

type ViewMode = 'card' | 'list';

// 카드 뷰 컴포넌트
function ComplexCard({ complex }: { complex: Complex }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: complex.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      className="bg-white rounded-lg shadow hover:shadow-lg transition"
    >
      {/* 드래그 핸들 */}
      <div
        {...listeners}
        className="bg-gray-50 px-4 py-2 rounded-t-lg border-b cursor-move hover:bg-gray-100 flex items-center justify-between"
      >
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
          </svg>
          <span>드래그하여 순서 변경</span>
        </div>
      </div>

      {/* 카드 내용 */}
      <a href={`/complexes/${complex.complex_id}`} className="block p-6">
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
    </div>
  );
}

// 리스트 뷰 컴포넌트
function ComplexListItem({ complex }: { complex: Complex }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: complex.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      className="bg-white rounded-lg shadow hover:shadow-md transition"
    >
      <div className="flex items-center">
        {/* 드래그 핸들 */}
        <div
          {...listeners}
          className="px-4 py-6 cursor-move hover:bg-gray-50 border-r"
        >
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
          </svg>
        </div>

        {/* 리스트 내용 */}
        <a href={`/complexes/${complex.complex_id}`} className="flex-1 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{complex.complex_name}</h3>
              <div className="flex gap-6 text-sm text-gray-600">
                <span>{complex.complex_type}</span>
                <span>{complex.total_households}세대</span>
                <span>{complex.total_dongs}개동</span>
                <span>{complex.min_area}㎡ ~ {complex.max_area}㎡</span>
              </div>
            </div>
            {complex.min_price && complex.max_price && (
              <div className="text-right">
                <div className="text-sm text-gray-600 mb-1">매매가</div>
                <div className="text-lg font-semibold text-blue-600">
                  {(complex.min_price / 10000).toFixed(1)}억 ~ {(complex.max_price / 10000).toFixed(1)}억
                </div>
              </div>
            )}
          </div>
        </a>
      </div>
    </div>
  );
}

export default function ComplexesPage() {
  const [complexes, setComplexes] = useState<Complex[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('card');

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    const fetchComplexes = async () => {
      try {
        const response = await complexAPI.getAll();
        const fetchedComplexes = response.data;

        // localStorage에서 저장된 순서 불러오기
        const savedOrder = localStorage.getItem('complexOrder');
        if (savedOrder) {
          try {
            const orderIds = JSON.parse(savedOrder) as number[];
            // 저장된 순서대로 정렬
            const orderedComplexes = orderIds
              .map(id => fetchedComplexes.find(c => c.id === id))
              .filter(Boolean) as Complex[];

            // 새로 추가된 단지는 맨 뒤에 추가
            const newComplexes = fetchedComplexes.filter(
              c => !orderIds.includes(c.id)
            );

            setComplexes([...orderedComplexes, ...newComplexes]);
          } catch (e) {
            console.error('순서 복원 실패:', e);
            setComplexes(fetchedComplexes);
          }
        } else {
          setComplexes(fetchedComplexes);
        }
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchComplexes();
  }, []);

  // 뷰 모드를 localStorage에 저장
  useEffect(() => {
    const savedViewMode = localStorage.getItem('complexViewMode') as ViewMode;
    if (savedViewMode) {
      setViewMode(savedViewMode);
    }
  }, []);

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem('complexViewMode', mode);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setComplexes((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);

        const newOrder = arrayMove(items, oldIndex, newIndex);

        // localStorage에 새로운 순서 저장
        const orderIds = newOrder.map(item => item.id);
        localStorage.setItem('complexOrder', JSON.stringify(orderIds));

        return newOrder;
      });
    }
  };

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
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">단지 목록</h1>
            <p className="text-gray-600 mt-2">등록된 아파트 단지 목록입니다</p>
          </div>
          <div className="flex items-center gap-3">
            {/* 뷰 모드 전환 버튼 */}
            <div className="flex border border-gray-300 rounded-lg overflow-hidden">
              <button
                onClick={() => handleViewModeChange('card')}
                className={`px-4 py-2 text-sm font-medium transition ${
                  viewMode === 'card'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              <button
                onClick={() => handleViewModeChange('list')}
                className={`px-4 py-2 text-sm font-medium transition ${
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>

            <a
              href="/complexes/new"
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
            >
              + 새 단지 추가
            </a>
          </div>
        </div>
      </div>

      {/* 드래그 앤 드롭 컨텍스트 */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={complexes.map((c) => c.id)}
          strategy={viewMode === 'card' ? rectSortingStrategy : verticalListSortingStrategy}
        >
          {viewMode === 'card' ? (
            // 카드 뷰
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {complexes.map((complex) => (
                <ComplexCard key={complex.id} complex={complex} />
              ))}
            </div>
          ) : (
            // 리스트 뷰
            <div className="space-y-4">
              {complexes.map((complex) => (
                <ComplexListItem key={complex.id} complex={complex} />
              ))}
            </div>
          )}
        </SortableContext>
      </DndContext>

      {complexes.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-600">등록된 단지가 없습니다.</p>
          <a
            href="/complexes/new"
            className="inline-block mt-4 text-blue-600 hover:underline"
          >
            첫 단지를 추가해보세요 →
          </a>
        </div>
      )}
    </div>
  );
}
