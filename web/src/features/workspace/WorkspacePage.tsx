import { useEffect, useState } from "react";
import {
  deleteTripItem,
  getTripDetail,
  startTripGeneration,
  updateTripItem,
  type UpdateTripItemPayload,
} from "../../api/trips";
import { ApiError } from "../../api/client";
import { getJobStatus } from "../../api/jobs";
import { WAnnotation, WBtn, WImgBox } from "../../components/ui/Primitives";
import type { Itinerary, ItineraryItem, StopType } from "../../types/itinerary";
import { STOP_TYPE_LABELS } from "../../types/itinerary";
import { LOCAL_TRANSPORT_LABELS } from "../../types/trip";
import { AttractionCard } from "./AttractionCard";
import { RightPanel } from "./RightPanel";

function hasPendingGeneratedDays(itinerary: Itinerary | null) {
  if (!itinerary) return false;

  return itinerary.days.some((day) => day.items.some((item) => item.verification === "placeholder"));
}

type EditingItemState = {
  day: number;
  item: ItineraryItem;
  form: Required<Pick<UpdateTripItemPayload, "title" | "startTime" | "durationMin" | "stopType" | "cost" | "reason">>;
};

export function PageWorkspace({
  tripId,
  onOpenModal,
  onOutput,
  onTripChanged,
}: {
  tripId: string;
  onOpenModal: (item: ItineraryItem) => void;
  onOutput: () => void;
  onTripChanged: () => void;
}) {
  const [activeDay, setActiveDay] = useState(0);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  // 409 = 行程存在但从未生成过内容，这不是错误，是一个可以就地补救的状态
  const [needsGeneration, setNeedsGeneration] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationMessage, setGenerationMessage] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [mutationMessage, setMutationMessage] = useState("");
  const [editingItem, setEditingItem] = useState<EditingItemState | null>(null);

  useEffect(() => {
    let ignore = false;

    async function loadTripDetail() {
      setIsLoading(true);
      setErrorMessage("");
      setNeedsGeneration(false);

      try {
        const detail = await getTripDetail(tripId);
        if (!ignore) {
          setItinerary(detail);
          setActiveDay((current) => Math.min(current, detail.days.length - 1));
        }
      } catch (error) {
        if (!ignore) {
          if (error instanceof ApiError && error.status === 409) {
            setNeedsGeneration(true);
          } else {
            setErrorMessage(error instanceof Error ? error.message : "行程详情加载失败");
          }
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    loadTripDetail();

    return () => {
      ignore = true;
    };
  }, [tripId, reloadKey]);

  useEffect(() => {
    if (!hasPendingGeneratedDays(itinerary)) return;

    const timer = window.setInterval(async () => {
      try {
        const detail = await getTripDetail(tripId);
        setItinerary(detail);
        setActiveDay((current) => Math.min(current, detail.days.length - 1));
      } catch {
        // Keep the current partial itinerary visible while background generation continues.
      }
    }, 5000);

    return () => window.clearInterval(timer);
  }, [itinerary, tripId]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="rounded-xl border border-slate-200 bg-white px-8 py-6 text-center shadow-sm">
          <p className="text-sm font-medium text-slate-800">正在加载行程工作区...</p>
          <p className="text-xs font-mono text-slate-400 mt-1">正在同步行程详情</p>
        </div>
      </div>
    );
  }

  async function handleGenerate() {
    setIsGenerating(true);
    setGenerationMessage("正在提交生成任务");

    try {
      const { jobId } = await startTripGeneration(tripId);

      for (let attempt = 0; attempt < 60; attempt += 1) {
        const job = await getJobStatus(jobId, tripId);
        setGenerationMessage(job.message);

        if (job.status === "succeeded") {
          setReloadKey((key) => key + 1);
          return;
        }

        if (job.status === "failed") {
          setGenerationMessage(job.message || "生成失败，请稍后重试");
          return;
        }

        await new Promise((resolve) => window.setTimeout(resolve, 1000));
      }

      setGenerationMessage("生成超时，请稍后重试");
    } catch (error) {
      setGenerationMessage(error instanceof Error ? error.message : "生成失败");
    } finally {
      setIsGenerating(false);
    }
  }

  if (needsGeneration) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="max-w-sm rounded-xl border border-slate-200 bg-white px-8 py-7 text-center shadow-sm">
          <p className="text-sm font-medium text-slate-800">这个行程还没有生成内容</p>
          <p className="mt-1.5 text-xs text-slate-500">生成后即可在工作区逐日编辑安排。</p>
          <div className="mt-4">
            <WBtn label={isGenerating ? "生成中..." : "立即生成行程"} primary onClick={() => void handleGenerate()} />
          </div>
          {generationMessage && <p className="mt-3 text-[11px] font-mono text-slate-400">{generationMessage}</p>}
        </div>
      </div>
    );
  }

  if (errorMessage || !itinerary) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="border border-red-200 bg-red-50 px-8 py-6 text-center">
          <p className="text-sm font-medium text-red-700">{errorMessage || "没有找到行程详情"}</p>
          <button
            onClick={() => setReloadKey((key) => key + 1)}
            className="mt-3 border border-red-300 bg-white px-3 py-1.5 text-xs font-mono text-red-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  const day = itinerary.days[activeDay] ?? itinerary.days[0];

  const handleDeleteItem = async (item: ItineraryItem) => {
    const confirmed = window.confirm(`确定从第${day.day}天删除「${item.title}」吗？`);
    if (!confirmed) return;

    setMutationMessage("");

    try {
      const updated = await deleteTripItem(tripId, day.day, item.id);
      setItinerary(updated);
      const nextActiveDay = Math.min(activeDay, updated.days.length - 1);
      setActiveDay(Math.max(nextActiveDay, 0));
      onTripChanged();
    } catch (error) {
      setMutationMessage(error instanceof Error ? error.message : "删除景点失败");
    }
  };

  const openEditItem = (item: ItineraryItem) => {
    setEditingItem({
      day: day.day,
      item,
      form: {
        title: item.title,
        startTime: item.startTime,
        durationMin: item.durationMin,
        stopType: item.stopType,
        cost: item.cost,
        reason: item.reason ?? "",
      },
    });
  };

  const patchEditingForm = (patch: Partial<EditingItemState["form"]>) => {
    setEditingItem((current) => (current ? { ...current, form: { ...current.form, ...patch } } : current));
  };

  const handleSaveItem = async () => {
    if (!editingItem) return;

    setMutationMessage("");

    try {
      const updated = await updateTripItem(tripId, editingItem.day, editingItem.item.id, editingItem.form);
      setItinerary(updated);
      setEditingItem(null);
      onTripChanged();
    } catch (error) {
      setMutationMessage(error instanceof Error ? error.message : "编辑景点失败");
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* < 1024px 时改用中栏顶部的横向日程条 */}
      <div className="hidden lg:flex w-40 border-r border-slate-200 bg-white flex-col shrink-0">
        <div className="p-3 border-b border-slate-100">
          <WAnnotation text="日程导航" />
          <p className="text-xs font-semibold text-slate-700 mt-0.5">
            {itinerary.destination} · {itinerary.days.length}天
          </p>
        </div>
        {itinerary.days.map((dayItem, index) => (
          <button
            key={dayItem.day}
            onClick={() => setActiveDay(index)}
            className={`text-left px-3 py-2.5 text-xs font-mono border-b border-slate-100 cursor-pointer transition-colors ${
              index === activeDay
                ? "bg-sky-50 text-sky-700 border-r-2 border-sky-500"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span className="block font-semibold">第{dayItem.day}天</span>
            <span className="text-[10px] opacity-70">{dayItem.date}</span>
          </button>
        ))}
        <div className="p-3 mt-auto border-t border-slate-100">
          <div className="rounded-md border border-slate-200 bg-slate-50 px-2 py-2 text-center text-[10px] font-mono text-slate-400">
            天数由创建信息生成
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="border-b border-slate-200 bg-white/95 px-4 py-3 shrink-0 shadow-sm shadow-slate-200/50">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span className="truncate text-sm font-semibold text-slate-900">
                第{day.day}天 · {day.date} · {day.title}
              </span>
              <span className="hidden xl:block">
                <WAnnotation text="← 当天主题自动生成" />
              </span>
            </div>
            <div className="hidden xl:block">
              <WAnnotation text="复杂调整请使用下方 AI 输入框" />
            </div>
            {/* 右栏在 < 1280px 时隐藏，主 CTA 移到这里，避免用户找不到「输出方案」 */}
            <div className="xl:hidden shrink-0">
              <WBtn label="输出行程方案 →" primary small onClick={onOutput} />
            </div>
          </div>

          {/* < 1024px 时替代左侧日程栏 */}
          <div className="lg:hidden -mb-1 mt-2.5 flex gap-1.5 overflow-x-auto pb-1">
            {itinerary.days.map((dayItem, index) => (
              <button
                key={dayItem.day}
                onClick={() => setActiveDay(index)}
                className={`shrink-0 rounded-full border px-3 py-1 text-[11px] font-mono transition-colors ${
                  index === activeDay
                    ? "border-sky-500 bg-sky-600 text-white"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                第{dayItem.day}天
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-auto p-4">
          {mutationMessage && (
            <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-mono text-red-700">
              {mutationMessage}
            </div>
          )}
          {hasPendingGeneratedDays(itinerary) && (
            <div className="mb-3 rounded-lg border border-sky-100 bg-sky-50 px-3 py-2 text-xs text-sky-700">
              第 1 天已可编辑，后续天数正在后台继续生成，会自动同步到这里。
            </div>
          )}
          <div className="flex items-center gap-2 mb-4">
            <WImgBox className="w-4 h-4" label="" />
            {/* TODO(backend): 住宿信息尚未进入数据模型，暂以目的地兜底 */}
            <span className="text-xs font-mono text-slate-500">出发点：{itinerary.destination}</span>
          </div>

          {day.items.map((item, index) => (
            <div key={item.id} className="flex gap-3 mb-3">
              <div className="flex flex-col items-center w-8 shrink-0">
                <div className="w-3 h-3 border-2 border-sky-600 bg-white rounded-full mt-2" />
                {index < day.items.length - 1 && <div className="w-0.5 flex-1 bg-sky-100 my-1" />}
              </div>
              <div className="flex-1">
                {item.transitMinutes != null && (
                  <div className="flex items-center gap-2 mb-2 ml-2">
                    <div className="w-3 h-3 rounded bg-slate-200 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded bg-sky-500" />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">
                      {item.transitMode ? LOCAL_TRANSPORT_LABELS[item.transitMode] : "移动"} {item.transitMinutes} 分钟
                    </span>
                  </div>
                )}
                <AttractionCard
                  item={item}
                  onClick={() => onOpenModal(item)}
                  onDelete={() => void handleDeleteItem(item)}
                  onEdit={() => openEditItem(item)}
                />
              </div>
            </div>
          ))}

          <div className="mt-6 pt-4 border-t border-dashed border-slate-200">
            <div className="mb-2 flex items-center justify-between">
              <WAnnotation text="Editing Agent" />
            </div>
            <div className="mt-1 flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 shadow-sm">
              <WImgBox className="w-6 h-6 rounded-full shrink-0" label="" />
              <div className="min-w-0">
                <p className="text-xs font-medium text-slate-700">AI 调整功能正在重构</p>
                <p className="mt-0.5 text-[10px] font-mono text-slate-400">
                  当前保留手动编辑和删除；新的 Editing Agent 会在后续重新接入。
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <RightPanel day={day} onOutput={onOutput} />
      {editingItem && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/35">
          <div className="w-[520px] rounded-xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/20">
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
              <div>
                <WAnnotation text={`第${editingItem.day}天 · 景点编辑`} />
                <h2 className="text-sm font-semibold text-slate-900">编辑景点</h2>
              </div>
              <button
                onClick={() => setEditingItem(null)}
                className="rounded-md border border-slate-200 px-2 py-1 text-xs font-mono text-slate-500 hover:bg-slate-50"
              >
                关闭
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3 p-5">
              <label className="col-span-2 flex flex-col gap-1 text-xs font-medium text-slate-600">
                标题
                <input
                  value={editingItem.form.title}
                  onChange={(event) => patchEditingForm({ title: event.target.value })}
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                />
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
                开始时间
                <input
                  value={editingItem.form.startTime}
                  onChange={(event) => patchEditingForm({ startTime: event.target.value })}
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                />
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
                停留时长（分钟）
                <input
                  type="number"
                  min={0}
                  value={editingItem.form.durationMin}
                  onChange={(event) => patchEditingForm({ durationMin: Number(event.target.value) })}
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                />
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
                类型
                <select
                  value={editingItem.form.stopType}
                  onChange={(event) => patchEditingForm({ stopType: event.target.value as StopType })}
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                >
                  {(Object.entries(STOP_TYPE_LABELS) as [StopType, string][]).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
                费用
                <input
                  type="number"
                  value={editingItem.form.cost}
                  onChange={(event) => patchEditingForm({ cost: Number(event.target.value) })}
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                />
              </label>
              <label className="col-span-2 flex flex-col gap-1 text-xs font-medium text-slate-600">
                推荐理由 / 备注
                <textarea
                  value={editingItem.form.reason}
                  onChange={(event) => patchEditingForm({ reason: event.target.value })}
                  className="min-h-20 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                />
              </label>
            </div>
            <div className="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">
              <WBtn label="取消" small onClick={() => setEditingItem(null)} />
              <WBtn label="保存修改" small primary onClick={() => void handleSaveItem()} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
