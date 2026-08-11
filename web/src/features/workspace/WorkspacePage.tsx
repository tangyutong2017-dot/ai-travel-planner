import { useEffect, useState, type ReactNode } from "react";
import { deleteTripItem, getTripDetail, startTripGeneration, updateTripItem, type UpdateTripItemPayload } from "../../api/trips";
import { ApiError } from "../../api/client";
import { getJobStatus } from "../../api/jobs";
import { Divider, WAnnotation, WBtn, WImgBox } from "../../components/ui/Primitives";
import type { DayPlan, Itinerary, ItineraryItem } from "../../types/itinerary";

function hasPendingGeneratedDays(itinerary: Itinerary | null) {
  if (!itinerary) return false;

  return itinerary.days.some((day) =>
    day.items.some((item) => item.type === "AI规划" || item.reason?.includes("占位数据") || item.reason?.includes("下一步由 LangGraph agent"))
  );
}

function AttractionCard({ item, onClick, onDelete, onEdit }: {
  item: ItineraryItem;
  onClick: () => void;
  onDelete: () => void;
  onEdit: () => void;
}) {
  return (
    <div
      className="rounded-lg border border-slate-200 bg-white p-3 flex gap-3 cursor-pointer hover:border-sky-200 hover:shadow-md hover:shadow-sky-100/70 transition-all"
      onClick={onClick}
    >
      {item.imageUrl ? (
        <img className="h-14 w-16 shrink-0 rounded-md object-cover" src={item.imageUrl} alt={`${item.title} 景点图`} />
      ) : (
        <WImgBox className="w-16 h-14 shrink-0" label="景点图" />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-medium text-slate-800 leading-tight">{item.title}</p>
          <span className="rounded-full text-[10px] font-mono text-sky-700 border border-sky-200 bg-sky-50 px-2 py-0.5 shrink-0">{item.type}</span>
        </div>
        <p className="text-xs font-mono text-slate-500 mt-1">{item.startTime} - {item.endTime}</p>
        {item.address && (
          <p className="mt-1 truncate text-[10px] font-mono text-slate-400">地址 · {item.address}</p>
        )}
        <div className="flex items-center gap-2 mt-2">
          {/* 评分曾是写死的 4.2 + 四颗星。数据模型里没有评分字段，接入真实 POI 评分前不展示。 */}
          <span className="text-[10px] font-mono text-slate-500">预计 {item.durationLabel} · {item.cost === 0 ? "免费" : `¥${item.cost}`}</span>
        </div>
      </div>
      <div className="flex flex-col gap-1 shrink-0">
        <button
          onClick={(event) => {
            event.stopPropagation();
            onEdit();
          }}
          className="rounded text-[10px] font-mono text-slate-500 border border-slate-200 px-2 py-0.5 hover:bg-slate-50"
        >
          编辑
        </button>
        <button
          onClick={(event) => {
            event.stopPropagation();
            onDelete();
          }}
          className="rounded text-[10px] font-mono text-red-500 border border-red-100 px-2 py-0.5 hover:bg-red-50"
        >
          删除
        </button>
      </div>
    </div>
  );
}

type EditingItemState = {
  day: number;
  item: ItineraryItem;
  form: Required<Pick<UpdateTripItemPayload, "title" | "startTime" | "endTime" | "type" | "durationLabel" | "cost" | "reason">>;
};

function CollapsibleSection({
  title,
  badge,
  defaultOpen = false,
  children,
}: {
  title: string;
  badge?: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-slate-100">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3 py-2.5 cursor-pointer hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">{title}</span>
          {badge && (
            <span className="rounded-full text-[10px] font-mono text-slate-500 border border-slate-200 px-1.5 py-0.5 bg-slate-50">
              {badge}
            </span>
          )}
        </div>
        <span className="text-slate-400 font-mono text-xs">{open ? "▲" : "▼"}</span>
      </button>
      {open && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}

function RouteMiniMap({ day }: { day: DayPlan }) {
  const points = day.items
    .map((item, index) => item.location ? { item, index, lat: item.location.lat, lng: item.location.lng } : null)
    .filter((point): point is { item: ItineraryItem; index: number; lat: number; lng: number } => point !== null);

  if (points.length === 0) {
    return (
      <div className="flex h-36 w-full flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 text-center">
        <span className="text-[11px] font-medium text-slate-500">暂无坐标</span>
        <span className="mt-1 text-[10px] font-mono text-slate-400">生成真实 POI 后显示路线</span>
      </div>
    );
  }

  const minLat = Math.min(...points.map((point) => point.lat));
  const maxLat = Math.max(...points.map((point) => point.lat));
  const minLng = Math.min(...points.map((point) => point.lng));
  const maxLng = Math.max(...points.map((point) => point.lng));
  const latSpan = Math.max(maxLat - minLat, 0.01);
  const lngSpan = Math.max(maxLng - minLng, 0.01);
  const toSvgPoint = (point: { lat: number; lng: number }) => ({
    x: 18 + ((point.lng - minLng) / lngSpan) * 164,
    y: 122 - ((point.lat - minLat) / latSpan) * 104,
  });
  const svgPoints = points.map((point) => ({ ...point, ...toSvgPoint(point) }));

  return (
    <div className="relative h-36 w-full overflow-hidden rounded-lg border border-sky-100 bg-[linear-gradient(135deg,#f8fafc,#e0f2fe)]">
      <svg viewBox="0 0 200 140" className="h-full w-full">
        <defs>
          <pattern id={`map-grid-${day.day}`} width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#cbd5e1" strokeWidth="0.35" opacity="0.8" />
          </pattern>
        </defs>
        <rect width="200" height="140" fill={`url(#map-grid-${day.day})`} />
        <polyline
          points={svgPoints.map((point) => `${point.x},${point.y}`).join(" ")}
          fill="none"
          stroke="#0284c7"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.85"
        />
        {svgPoints.map((point) => (
          <g key={point.item.id}>
            <circle cx={point.x} cy={point.y} r="8" fill="white" stroke="#0284c7" strokeWidth="2" />
            <text x={point.x} y={point.y + 3.5} textAnchor="middle" className="fill-sky-700 text-[9px] font-bold">
              {point.index + 1}
            </text>
          </g>
        ))}
      </svg>
      <div className="absolute left-2 top-2 rounded-full border border-white/80 bg-white/90 px-2 py-0.5 text-[10px] font-mono text-slate-600 shadow-sm">
        {points.length} 个坐标点
      </div>
      <div className="absolute bottom-2 left-2 right-2 truncate rounded-md bg-white/85 px-2 py-1 text-[10px] text-slate-500 shadow-sm">
        {points.map((point) => point.item.title).join(" → ")}
      </div>
    </div>
  );
}

function RightPanel({ day, onOutput }: { day: DayPlan; onOutput: () => void }) {
  const budgetEntries = Object.entries(day.budget);
  const budgetTotal = budgetEntries.reduce((sum, [, value]) => sum + value, 0);
  const formatKm = (value: number) => `${Number(value.toFixed(1))} km`;
  const dataStats = [
    ["POI", day.items.filter((item) => item.poiId).length],
    ["坐标", day.items.filter((item) => item.location).length],
    ["图片", day.items.filter((item) => item.imageUrl).length],
  ] as const;
  const totalItems = Math.max(day.items.length, 1);

  return (
    // < 1280px 时隐藏：四栏固定宽度合计 640px，再窄中间时间线会被压成竖排文字。
    // 隐藏后「输出行程方案」CTA 由中栏头部的 xl:hidden 按钮接管。
    <div className="hidden xl:flex w-64 border-l border-slate-200 bg-white/90 backdrop-blur flex-col shrink-0 overflow-auto">
      <CollapsibleSection title="地图预览" badge="路线" defaultOpen={true}>
        <RouteMiniMap day={day} />
        <div className="mt-2 space-y-0.5">
          {[
            ["总距离", formatKm(day.route.distanceKm)],
            ["步行", formatKm(day.route.walkKm)],
            ["交通", formatKm(day.route.transitKm)],
            ["耗时", day.route.durationLabel],
          ].map(([key, value]) => (
            <div key={key} className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>{key}</span><span className="font-medium text-slate-700">{value}</span>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      <CollapsibleSection title="天气预报" badge={`${day.date} ${day.weather.desc}`} defaultOpen={true}>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-center">
          <p className="text-[10px] font-mono text-slate-400">{day.date}</p>
          <p className="text-xl my-0.5">{day.weather.icon}</p>
          <p className="text-[10px] font-mono text-slate-600">{day.weather.desc}</p>
          <p className="text-[10px] font-mono text-slate-400">{day.weather.range}</p>
        </div>
        {day.weather.tip && <p className="text-[10px] font-mono text-slate-400 mt-2">{day.weather.tip}</p>}
      </CollapsibleSection>

      <CollapsibleSection title="预算概览" badge={`¥ ${budgetTotal}`} defaultOpen={false}>
        <div className="space-y-1.5">
          {budgetEntries.map(([key, value]) => (
            <div key={key}>
              <div className="flex justify-between text-[10px] font-mono text-slate-600 mb-0.5">
                <span>{key}</span><span>¥ {value}</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-sky-500" style={{ width: `${Math.round((value / budgetTotal) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-2 pt-2 border-t border-slate-200 flex justify-between text-xs font-semibold font-mono text-slate-800">
          <span>合计</span><span>¥ {budgetTotal}</span>
        </div>
      </CollapsibleSection>

      <CollapsibleSection title="数据质量" badge={`${day.items.length} 项`} defaultOpen={false}>
        <div className="space-y-2">
          {dataStats.map(([label, count]) => (
            <div key={label}>
              <div className="mb-1 flex justify-between text-[10px] font-mono text-slate-600">
                <span>{label}</span>
                <span>{count}/{day.items.length}</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.round((count / totalItems) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
        <p className="mt-2 text-[10px] text-slate-400">缺失项可通过下方 AI 输入框补充或重新生成。</p>
      </CollapsibleSection>

      <CollapsibleSection title="路线备注" defaultOpen={false}>
        <div className="space-y-1.5">
          {day.items
            .filter((item) => item.reason)
            .slice(0, 3)
            .map((item) => (
              <div key={item.id} className="flex gap-2 text-[10px] font-mono text-slate-600">
                <span className="text-sky-300 shrink-0">·</span>
                <span>{item.reason}</span>
              </div>
            ))}
        </div>
      </CollapsibleSection>

      <div className="mt-auto border-t border-slate-100 p-3">
        <WBtn label="输出行程方案 →" primary className="w-full" onClick={onOutput} />
        <WAnnotation text="导出 PDF / 分享链接" />
      </div>
    </div>
  );
}

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
            <WBtn
              label={isGenerating ? "生成中..." : "立即生成行程"}
              primary
              onClick={() => void handleGenerate()}
            />
          </div>
          {generationMessage && (
            <p className="mt-3 text-[11px] font-mono text-slate-400">{generationMessage}</p>
          )}
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
        endTime: item.endTime,
        type: item.type,
        durationLabel: item.durationLabel,
        cost: item.cost,
        reason: item.reason ?? "",
      },
    });
  };

  const patchEditingForm = (patch: Partial<EditingItemState["form"]>) => {
    setEditingItem((current) => current ? { ...current, form: { ...current.form, ...patch } } : current);
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
          <p className="text-xs font-semibold text-slate-700 mt-0.5">{itinerary.destination} · {itinerary.days.length}天</p>
        </div>
        {itinerary.days.map((dayItem, index) => (
          <button
            key={dayItem.day}
            onClick={() => setActiveDay(index)}
            className={`text-left px-3 py-2.5 text-xs font-mono border-b border-slate-100 cursor-pointer transition-colors ${
              index === activeDay ? "bg-sky-50 text-sky-700 border-r-2 border-sky-500" : "text-slate-600 hover:bg-slate-50"
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
              <span className="truncate text-sm font-semibold text-slate-900">第{day.day}天 · {day.date} · {day.title}</span>
              <span className="hidden xl:block"><WAnnotation text="← 当天主题自动生成" /></span>
            </div>
            <div className="hidden xl:block"><WAnnotation text="复杂调整请使用下方 AI 输入框" /></div>
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
                {item.transitFromPrev && (
                  <div className="flex items-center gap-2 mb-2 ml-2">
                    <div className="w-3 h-3 rounded bg-slate-200 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded bg-sky-500" />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">{item.transitFromPrev}</span>
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
                <p className="mt-0.5 text-[10px] font-mono text-slate-400">当前保留手动编辑和删除；新的 Editing Agent 会在后续重新接入。</p>
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
                结束时间
                <input
                  value={editingItem.form.endTime}
                  onChange={(event) => patchEditingForm({ endTime: event.target.value })}
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                />
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
                类型
                <input
                  value={editingItem.form.type}
                  onChange={(event) => patchEditingForm({ type: event.target.value })}
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                />
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

export function ModalAttraction({ item, onClose }: { item: ItineraryItem; onClose: () => void }) {
  const detailRows = [
    ["游览时间", `${item.startTime} - ${item.endTime}`],
    ["建议停留", item.durationLabel],
    ["费用", item.cost === 0 ? "免费" : `¥${item.cost}`],
    ["地址", item.address || "暂无地址"],
    ["交通", item.transitFromPrev || "首站 / 暂无上一站交通"],
    ["坐标", item.location ? `${item.location.lat}, ${item.location.lng}` : "暂无坐标"],
    ["来源", item.source === "amap" ? "高德 POI" : item.source === "deepseek" ? "DeepSeek" : "系统生成"],
  ];

  return (
    <div className="absolute inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="w-[680px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl shadow-slate-950/20"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <div>
            <WAnnotation text="景点详情" />
            <h2 className="text-base font-bold text-slate-900">{item.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 text-lg font-mono text-slate-500 hover:bg-slate-50 hover:text-slate-900"
          >
            ×
          </button>
        </div>

        <div className="p-5">
          <div className="flex gap-4 mb-4">
            {item.imageUrl ? (
              <img className="h-36 w-52 shrink-0 rounded-lg object-cover" src={item.imageUrl} alt={`${item.title} 主图`} />
            ) : (
              <WImgBox className="w-52 h-36 shrink-0 rounded-lg" label="景点主图" />
            )}
            <div className="flex-1">
              <div className="flex flex-wrap gap-1.5 mb-3">
                {[item.type, item.source === "amap" ? "高德验证" : "AI生成", item.poiId ? "POI" : "未匹配POI"].map((tag) => (
                  <span key={tag} className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-mono text-slate-600">{tag}</span>
                ))}
              </div>
              <div className="space-y-1.5">
                {detailRows.map(([key, value]) => (
                  <div key={key} className="flex gap-2 text-xs font-mono">
                    <span className="text-slate-400 w-20 shrink-0">{key}</span>
                    <span className="text-slate-700">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mb-4">
            <p className="text-xs font-semibold text-slate-700 mb-1">推荐理由</p>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs text-slate-600 leading-relaxed">
                {item.reason || "暂无推荐理由。后续可由 Editing Agent 或景点详情服务补充更完整介绍。"}
              </p>
            </div>
          </div>

          <div className="mb-4">
            <p className="text-xs font-semibold text-slate-700 mb-1">数据状态</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                ["图片", item.imageUrl ? "已获取" : "暂无"],
                ["坐标", item.location ? "已获取" : "暂无"],
                ["POI", item.poiId ? item.poiId : "暂无"],
              ].map(([key, value]) => (
                <div key={key} className="rounded-lg border border-slate-200 bg-white p-2">
                  <p className="text-[10px] font-mono text-slate-400">{key}</p>
                  <p className="mt-0.5 truncate text-xs font-medium text-slate-700">{value}</p>
                </div>
              ))}
            </div>
          </div>

          <Divider className="mb-4" />
          <div className="flex gap-2 justify-end">
            <WBtn label="复制位置" small onClick={() => {
              if (item.location) void navigator.clipboard?.writeText(`${item.location.lat},${item.location.lng}`);
            }} />
            <WBtn label="✓ 已在行程中" primary small />
          </div>
        </div>
      </div>
    </div>
  );
}
