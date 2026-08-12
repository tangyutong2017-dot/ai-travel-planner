import { useEffect, useMemo, useState, type ReactNode } from "react";
import { getTripDetail } from "../../api/trips";
import { Divider, WBtn, WImgBox } from "../../components/ui/Primitives";
import type { DayPlan, Itinerary } from "../../types/itinerary";
import { STOP_TYPE_LABELS, endTimeOf, formatDuration } from "../../types/itinerary";
import { LOCAL_TRANSPORT_LABELS } from "../../types/trip";

type OutputPageId = "cover" | number;

function PrintPage({
  itinerary,
  pageNum,
  total,
  children,
}: {
  itinerary: Itinerary;
  pageNum: number;
  total: number;
  children: ReactNode;
}) {
  return (
    <div className="relative mb-2">
      <div
        className="absolute inset-0 flex items-center justify-center pointer-events-none z-10 select-none"
        style={{ transform: "rotate(-30deg)" }}
      >
        <span className="text-5xl font-bold text-slate-200 tracking-widest opacity-50 whitespace-nowrap">预览版本</span>
      </div>

      <div
        className="bg-white shadow-xl shadow-slate-950/20 border border-slate-200 relative overflow-hidden"
        style={{ minHeight: "297mm", width: "210mm", margin: "0 auto" }}
      >
        <div className="border-b-2 border-slate-900 px-10 py-3 flex items-center justify-between">
          <span className="text-xs font-mono font-bold tracking-widest text-slate-900 uppercase">
            {itinerary.title}
          </span>
          <span className="text-xs font-mono text-slate-400">AI 行程规划 · 仅供参考</span>
        </div>

        <div className="px-10 py-8">{children}</div>

        <div className="absolute bottom-0 left-0 right-0 border-t border-slate-200 px-10 py-2 flex items-center justify-between bg-white">
          <span className="text-[10px] font-mono text-slate-400">由 AI 行程规划生成</span>
          <span className="text-[10px] font-mono text-slate-400">
            {pageNum} / {total}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 my-4 px-4">
        <div className="flex-1 border-t-2 border-dashed border-slate-400" />
        <span className="text-[10px] font-mono text-slate-400 bg-slate-300 px-2 py-0.5 whitespace-nowrap">
          分页线 · 第 {pageNum} 页结束
        </span>
        <div className="flex-1 border-t-2 border-dashed border-slate-400" />
      </div>
    </div>
  );
}

/** 成人/儿童/婴幼儿分别展示——原先只输出总数，2 大 1 小会写成「成人 3 人」。 */
function travelerLabel(t: Itinerary["travelers"]) {
  return [
    t.adults ? `成人 ${t.adults} 人` : "",
    t.children ? `儿童 ${t.children} 人` : "",
    t.infants ? `婴幼儿 ${t.infants} 人` : "",
  ]
    .filter(Boolean)
    .join(" · ");
}

function CoverPage({ itinerary, totalPages }: { itinerary: Itinerary; totalPages: number }) {
  return (
    <PrintPage itinerary={itinerary} pageNum={1} total={totalPages}>
      <div className="text-center mb-8">
        <WImgBox className="w-full h-40 mb-6 rounded-lg" label={`封面 · ${itinerary.destination}`} />
        <h1 className="text-3xl font-bold text-slate-950 mb-2 leading-tight">{itinerary.title}</h1>
        <p className="text-sm font-mono text-slate-500 mb-5">
          {itinerary.dateRange} · {travelerLabel(itinerary.travelers)}
        </p>
        <div className="flex justify-center gap-3 mb-8">
          {itinerary.interests.map((tag) => (
            <span
              key={tag}
              className="text-xs border border-sky-200 bg-sky-50 px-3 py-1 font-mono text-sky-700 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          ["目的地", itinerary.destination],
          ["出行天数", `${itinerary.days.length} 天`],
          ["旅行人数", travelerLabel(itinerary.travelers)],
        ].map(([key, value]) => (
          <div key={key} className="border border-slate-200 rounded-lg p-4 text-center">
            <p className="text-[10px] font-mono text-slate-400 mb-1 uppercase tracking-widest">{key}</p>
            <p className="text-base font-bold text-slate-900">{value}</p>
          </div>
        ))}
      </div>

      <p className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-3">每日概要</p>
      {itinerary.days.map((day) => (
        <div key={day.day} className="flex items-center gap-4 py-2.5 border-b border-slate-100">
          <span className="text-xs font-mono font-bold text-slate-700 w-12 shrink-0">第{day.day}天</span>
          <span className="text-xs font-mono text-slate-400 w-16 shrink-0">{day.date}</span>
          <span className="text-sm text-slate-800 flex-1">{day.title}</span>
          <span className="text-sm">{day.weather.icon}</span>
        </div>
      ))}
    </PrintPage>
  );
}

function DayOutputPage({
  itinerary,
  day,
  pageNum,
  totalPages,
}: {
  itinerary: Itinerary;
  day: DayPlan;
  pageNum: number;
  totalPages: number;
}) {
  return (
    <PrintPage itinerary={itinerary} pageNum={pageNum} total={totalPages}>
      <div className="flex items-end justify-between mb-6 pb-4 border-b border-slate-200">
        <div>
          <p className="text-[11px] font-mono text-slate-400 uppercase tracking-widest mb-1">DAY {day.day}</p>
          <h2 className="text-2xl font-bold text-slate-950 leading-tight">{day.title}</h2>
          <p className="text-sm font-mono text-slate-500 mt-1">
            {day.date} · {itinerary.destination}
          </p>
        </div>
        <div className="text-right">
          <div className="text-3xl mb-1">{day.weather.icon}</div>
          <p className="text-sm font-mono text-slate-700">{day.weather.desc}</p>
          <p className="text-xs font-mono text-slate-400">{day.weather.range}</p>
        </div>
      </div>

      <div className="flex gap-8">
        <div className="flex-1">
          <p className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-3">行程安排</p>
          {day.items.map((item, index) => (
            <div key={item.id} className="flex gap-3 mb-4">
              <div className="flex flex-col items-center w-5 shrink-0">
                <div className="w-3 h-3 border-2 border-sky-600 bg-white mt-1 shrink-0" />
                {index < day.items.length - 1 && <div className="w-px flex-1 bg-sky-100 mt-1" />}
              </div>
              <div className="flex-1 pb-2">
                {item.transitMinutes != null && (
                  <p className="text-[10px] font-mono text-slate-400 mb-1 -mt-0.5">
                    ↳ {item.transitMode ? LOCAL_TRANSPORT_LABELS[item.transitMode] : "移动"} {item.transitMinutes} 分钟
                  </p>
                )}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                    {/* 地址：带着这份 PDF 出门时最需要的信息，此前只在工作区显示 */}
                    {item.address && <p className="text-[10px] font-mono text-slate-400 mt-0.5">{item.address}</p>}
                    <div className="flex items-center gap-3 mt-0.5 text-[11px] font-mono text-slate-500">
                      <span>
                        {item.startTime}-{endTimeOf(item.startTime, item.durationMin)}
                      </span>
                      <span>· 约 {formatDuration(item.durationMin)}</span>
                      <span>· {item.cost === 0 ? "免费" : `¥ ${item.cost}`}</span>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono border border-sky-200 bg-sky-50 px-1.5 py-0.5 text-sky-700 shrink-0 rounded-full">
                    {STOP_TYPE_LABELS[item.stopType]}
                  </span>
                </div>
              </div>
            </div>
          ))}
          <div className="flex items-center gap-2 mt-1 ml-8">
            <span className="text-[10px] font-mono text-slate-400">
              {day.stay ? `↩ 返回住宿 · ${day.stay.area}` : "↩ 当晚无住宿安排"}
            </span>
          </div>
        </div>

        <div className="w-44 shrink-0 space-y-5">
          <div>
            <p className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-2">当日路线</p>
            <WImgBox className="w-full h-32 rounded-md" label="地图占位" />
            <div className="mt-1.5 space-y-0.5">
              {[
                ["通勤合计", `${day.items.reduce((n, i) => n + (i.transitMinutes ?? 0), 0)} 分钟`],
                ["停留合计", formatDuration(day.items.reduce((n, i) => n + i.durationMin, 0))],
              ].map(([key, value]) => (
                <div key={key} className="flex justify-between text-[10px] font-mono text-slate-500">
                  <span>{key}</span>
                  <span className="font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-2">天气详情</p>
            <p className="text-[10px] font-mono text-slate-500 leading-relaxed">
              {day.weather.tip ?? "天气适宜，注意合理安排体力。"}
            </p>
          </div>
        </div>
      </div>
    </PrintPage>
  );
}

export function PageOutput({ tripId, onBack }: { tripId: string; onBack: () => void }) {
  const [activePage, setActivePage] = useState<OutputPageId>("cover");
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let ignore = false;

    async function loadOutput() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const detail = await getTripDetail(tripId);
        if (!ignore) {
          setItinerary(detail);
          setActivePage("cover");
        }
      } catch (error) {
        if (!ignore) {
          setErrorMessage(error instanceof Error ? error.message : "输出预览加载失败");
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    loadOutput();
    return () => {
      ignore = true;
    };
  }, [tripId, reloadKey]);

  const pages = useMemo(() => {
    if (!itinerary) return [];
    return [
      { id: "cover" as const, label: "封面总览", sub: "行程概要" },
      ...itinerary.days.map((day, index) => ({ id: index, label: `第${day.day}天`, sub: day.date })),
    ];
  }, [itinerary]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-500">
        <div className="rounded-xl border border-slate-200 bg-white px-8 py-6 text-center shadow-sm">
          <p className="text-sm font-medium text-slate-800">正在加载输出预览...</p>
          <p className="text-xs font-mono text-slate-400 mt-1">正在同步行程详情</p>
        </div>
      </div>
    );
  }

  if (errorMessage || !itinerary) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-500">
        <div className="rounded-xl border border-red-200 bg-red-50 px-8 py-6 text-center">
          <p className="text-sm font-medium text-red-700">{errorMessage || "没有找到输出预览"}</p>
          <button
            onClick={() => setReloadKey((key) => key + 1)}
            className="mt-3 rounded-md border border-red-300 bg-white px-3 py-1.5 text-xs font-mono text-red-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  // 封面 1 页 + 每天 1 页（预算总表整页已移除）
  const totalPages = itinerary.days.length + 1;
  const activeIndex = pages.findIndex((page) => page.id === activePage);
  const canGoPrev = activeIndex > 0;
  const canGoNext = activeIndex >= 0 && activeIndex < pages.length - 1;

  return (
    <div className="flex-1 flex overflow-hidden">
      <div className="w-40 border-r border-slate-200 bg-white flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-2 h-2 bg-sky-500 rounded-full" />
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">只读预览</span>
          </div>
          <p className="text-xs font-semibold text-slate-700">输出方案</p>
        </div>

        <div className="flex-1 overflow-auto">
          {pages.map((page) => (
            <button
              key={page.id}
              onClick={() => setActivePage(page.id)}
              className={`w-full text-left px-3 py-2.5 text-xs font-mono border-b border-slate-100 cursor-pointer transition-colors ${
                activePage === page.id
                  ? "bg-sky-50 text-sky-700 border-r-2 border-sky-500"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <span className="block font-semibold">{page.label}</span>
              <span className="text-[10px] opacity-70">{page.sub}</span>
            </button>
          ))}
        </div>

        <div className="border-t border-slate-100 p-3 space-y-1.5 bg-slate-50">
          <p className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-2">导出</p>
          <WBtn label="导出 PDF" primary small className="w-full" />
          <WBtn label="分享链接" small className="w-full" />
          <WBtn label="同步日历" small className="w-full" />
          <Divider className="my-1" />
          <WBtn label="← 返回编辑" small className="w-full" onClick={onBack} />
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-slate-500 py-8 px-6">
        <div className="flex items-center justify-between mb-6 max-w-[210mm] mx-auto">
          <div className="flex items-center gap-2 bg-slate-700 text-slate-200 text-[11px] font-mono px-3 py-1.5 rounded-md">
            <span>🔒</span>
            <span>只读模式 · 如需修改请返回行程工作区</span>
          </div>
          <div className="flex gap-1.5">
            <button
              disabled={!canGoPrev}
              onClick={() => canGoPrev && setActivePage(pages[activeIndex - 1].id)}
              className="rounded-md bg-slate-600 disabled:bg-slate-400 text-white text-xs font-mono px-3 py-1.5 cursor-pointer hover:bg-slate-500"
            >
              ← 上一页
            </button>
            <button
              disabled={!canGoNext}
              onClick={() => canGoNext && setActivePage(pages[activeIndex + 1].id)}
              className="rounded-md bg-slate-600 disabled:bg-slate-400 text-white text-xs font-mono px-3 py-1.5 cursor-pointer hover:bg-slate-500"
            >
              下一页 →
            </button>
          </div>
        </div>

        {activePage === "cover" && <CoverPage itinerary={itinerary} totalPages={totalPages} />}
        {typeof activePage === "number" && (
          <DayOutputPage
            itinerary={itinerary}
            day={itinerary.days[activePage]}
            pageNum={activePage + 2}
            totalPages={totalPages}
          />
        )}
      </div>
    </div>
  );
}
