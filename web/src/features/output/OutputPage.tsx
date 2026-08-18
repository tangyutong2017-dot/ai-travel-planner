import { useEffect, useMemo, useState, type ReactNode } from "react";
import { getTripDetail } from "../../api/trips";
import { DayMap } from "../../components/ui/DayMap";
import type { DayPlan, Itinerary, ItineraryItem } from "../../types/itinerary";
import { STOP_TYPE_LABELS, TIME_SLOT_LABELS, formatDuration } from "../../types/itinerary";
import { LOCAL_TRANSPORT_SHORT } from "../../types/trip";

type OutputPageId = "cover" | number;

/** 衬线标题。
 *
 * 工作区通篇无衬线；输出页换衬线，翻过去的一瞬间就能感觉到「这是成品，
 * 不是工作界面」。中文衬线在各系统上的可用字体差异很大，故列一串回退。
 */
const SERIF = '"Songti SC", "Noto Serif SC", "Source Han Serif SC", "SimSun", Georgia, serif';

/** 高德实拍图来源杂乱、色调不统一——有的偏黄有的偏冷，原样铺满版面会很花。
 * 统一降饱和并压一点亮度，用一点点保真度换整页的视觉一致。 */
const PHOTO_FILTER = "saturate(0.82) contrast(1.04) brightness(0.98)";

function travelerLabel(t: Itinerary["travelers"]) {
  return [
    t.adults ? `成人 ${t.adults}` : "",
    t.children ? `儿童 ${t.children}` : "",
    t.infants ? `婴幼儿 ${t.infants}` : "",
  ]
    .filter(Boolean)
    .join(" · ");
}

function firstPhoto(itinerary: Itinerary): string | undefined {
  for (const day of itinerary.days) {
    for (const item of day.items) {
      if (item.imageUrl) return item.imageUrl;
    }
  }
  return undefined;
}

/** 一张 A4 纸。屏幕上按需显示，打印时由 .print-page 规则全部展开。 */
function Sheet({ visible, children }: { visible: boolean; children: ReactNode }) {
  return (
    <div
      className={`print-page mx-auto mb-6 w-[794px] bg-white shadow-xl shadow-slate-300/40 print:m-0 print:w-full print:shadow-none ${visible ? "block" : "hidden"}`}
      style={{ minHeight: "1123px" }}
    >
      {children}
    </div>
  );
}

// —— P1 总览 ——

function CoverSheet({ itinerary, visible }: { itinerary: Itinerary; visible: boolean }) {
  const cover = firstPhoto(itinerary);
  const totalStops = itinerary.days.reduce(
    (sum, day) => sum + day.items.filter((i) => !["flight", "train", "transfer"].includes(i.stopType)).length,
    0,
  );

  return (
    <Sheet visible={visible}>
      {/* 满幅封面图。没有照片时退回渐变，不留空洞 */}
      <div className="relative h-[300px] w-full overflow-hidden bg-slate-100">
        {cover ? (
          <img src={cover} alt="" className="h-full w-full object-cover" style={{ filter: PHOTO_FILTER }} />
        ) : (
          <div className="h-full w-full bg-[linear-gradient(135deg,#e2e8f0,#cbd5e1)]" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/10 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 px-16 pb-10">
          <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.3em] text-white/70">Itinerary</p>
          <h1 className="text-[40px] leading-tight text-white" style={{ fontFamily: SERIF }}>
            {itinerary.title}
          </h1>
        </div>
      </div>

      <div className="px-16 py-12">
        <div className="flex flex-wrap gap-x-12 gap-y-4 border-b border-slate-200 pb-8 text-[13px] text-slate-600">
          {[
            ["行程", itinerary.dateRange],
            ["出发", itinerary.originCity],
            ["目的地", itinerary.route.join(" · ") || itinerary.destination],
            ["同行", travelerLabel(itinerary.travelers)],
          ].map(([label, value]) => (
            <div key={label}>
              <p className="mb-1 text-[10px] uppercase tracking-widest text-slate-400">{label}</p>
              <p className="font-medium text-slate-800">{value}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-8 border-b border-slate-200 py-8 text-center">
          {[
            [String(itinerary.days.length), "天"],
            [String(totalStops), "个地点"],
            [String(itinerary.route.length || 1), "座城市"],
          ].map(([n, unit]) => (
            <div key={unit}>
              <p className="text-[34px] leading-none text-slate-900" style={{ fontFamily: SERIF }}>
                {n}
              </p>
              <p className="mt-2 text-[11px] tracking-widest text-slate-400">{unit}</p>
            </div>
          ))}
        </div>

        <section className="py-8">
          <h2 className="mb-5 text-[15px] tracking-wide text-slate-900" style={{ fontFamily: SERIF }}>
            行程速览
          </h2>
          <div className="space-y-3">
            {itinerary.days.map((day) => (
              <div key={day.day} className="print-avoid-break flex gap-5 border-b border-slate-100 pb-3">
                <span className="w-14 shrink-0 text-[22px] leading-none text-slate-300" style={{ fontFamily: SERIF }}>
                  {String(day.day).padStart(2, "0")}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-medium text-slate-800">{day.title}</p>
                  <p className="mt-0.5 text-[11px] text-slate-400">
                    {day.date} · {day.city} · {day.items.length} 项{day.stay ? ` · 宿 ${day.stay.area}` : ""}
                  </p>
                </div>
                <span className="shrink-0 text-[13px]">{day.weather.icon}</span>
              </div>
            ))}
          </div>
        </section>

        {itinerary.notes.length > 0 && (
          <section className="print-avoid-break border-t border-slate-200 pt-8">
            <h2 className="mb-5 text-[15px] tracking-wide text-slate-900" style={{ fontFamily: SERIF }}>
              出行提示
            </h2>
            <div className="space-y-2.5">
              {itinerary.notes.map((note, index) => (
                <div key={index} className="flex gap-3 text-[11.5px] leading-relaxed text-slate-600">
                  <span className={`shrink-0 ${note.kind === "alert" ? "text-amber-600" : "text-slate-400"}`}>
                    {note.kind === "alert" ? "⚠" : "ℹ"}
                  </span>
                  <span>{note.text}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </Sheet>
  );
}

// —— P2+ 每日 ——

function StopRow({ item }: { item: ItineraryItem }) {
  return (
    <div className="print-avoid-break flex gap-5 border-b border-slate-100 py-4">
      <div className="w-12 shrink-0 pt-0.5">
        <p className="text-[10px] tracking-widest text-slate-400">{TIME_SLOT_LABELS[item.timeSlot]}</p>
      </div>

      {item.imageUrl ? (
        <img
          src={item.imageUrl}
          alt=""
          className="h-16 w-20 shrink-0 rounded object-cover"
          style={{ filter: PHOTO_FILTER }}
        />
      ) : (
        <div className="flex h-16 w-20 shrink-0 items-center justify-center rounded bg-slate-50 text-[10px] text-slate-300">
          {STOP_TYPE_LABELS[item.stopType]}
        </div>
      )}

      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <p className="text-[14px] font-medium text-slate-900">{item.title}</p>
          {item.bookRequired && <span className="shrink-0 text-[10px] text-amber-600">需预约</span>}
          {item.optional && <span className="shrink-0 text-[10px] text-slate-400">可选</span>}
        </div>
        {item.address && <p className="mt-0.5 text-[10.5px] text-slate-400">{item.address}</p>}
        {item.reason && <p className="mt-1.5 text-[11px] leading-relaxed text-slate-600">{item.reason}</p>}
      </div>

      <div className="w-20 shrink-0 text-right text-[10.5px] text-slate-400">
        <p>{formatDuration(item.durationMin)}</p>
        <p className="mt-0.5">{item.cost === 0 ? "免费" : `¥${item.cost}`}</p>
        {item.transitMinutes != null && (
          <p className="mt-1.5 text-slate-300">
            {item.transitMode ? LOCAL_TRANSPORT_SHORT[item.transitMode] : "移动"} {item.transitMinutes}′
          </p>
        )}
      </div>
    </div>
  );
}

function DaySheet({ itinerary, day, visible }: { itinerary: Itinerary; day: DayPlan; visible: boolean }) {
  return (
    <Sheet visible={visible}>
      <div className="px-16 pb-12 pt-14">
        {/* 超大日期数字：最省力的视觉锚点 */}
        <div className="mb-8 flex items-end justify-between border-b border-slate-900 pb-5">
          <div className="flex items-end gap-5">
            <span className="text-[76px] leading-[0.8] text-slate-900" style={{ fontFamily: SERIF }}>
              {String(day.day).padStart(2, "0")}
            </span>
            <div className="pb-1.5">
              <h2 className="text-[19px] leading-tight text-slate-900" style={{ fontFamily: SERIF }}>
                {day.title}
              </h2>
              <p className="mt-1 text-[11px] tracking-wide text-slate-500">
                {day.date} · {day.city}
              </p>
            </div>
          </div>
          <div className="pb-1.5 text-right">
            <p className="text-[20px] leading-none">{day.weather.icon}</p>
            <p className="mt-1.5 text-[11px] text-slate-500">{day.weather.desc}</p>
            <p className="text-[10px] text-slate-400">{day.weather.range}</p>
          </div>
        </div>

        {/* 地图当主视觉，不当配图 */}
        <DayMap
          tripId={itinerary.tripId}
          dayNumber={day.day}
          hasCoordinates={day.items.some((item) => item.location)}
          // 高德静态图上限 1024×1024，接口层也按此校验；scale=2 时实际输出 2048×880，
          // 够 A4 宽幅清晰度
          width={1024}
          height={440}
          className="mb-9 h-[220px] w-full"
        />

        <div>
          {day.items.map((item) => (
            <StopRow key={item.id} item={item} />
          ))}
        </div>

        {day.stay && (
          <div className="print-avoid-break mt-8 border-t border-slate-200 pt-5">
            <p className="text-[10px] uppercase tracking-widest text-slate-400">当晚住宿</p>
            <p className="mt-1.5 text-[13px] font-medium text-slate-800">{day.stay.area}</p>
            {day.stay.reason && <p className="mt-1 text-[11px] leading-relaxed text-slate-500">{day.stay.reason}</p>}
          </div>
        )}
      </div>
    </Sheet>
  );
}

// —— 页面 ——

export function PageOutput({ tripId, onBack }: { tripId: string; onBack: () => void }) {
  const [activePage, setActivePage] = useState<OutputPageId>("cover");
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let ignore = false;

    async function load() {
      setIsLoading(true);
      setErrorMessage("");
      try {
        const detail = await getTripDetail(tripId);
        if (!ignore) setItinerary(detail);
      } catch (error) {
        if (!ignore) setErrorMessage(error instanceof Error ? error.message : "行程加载失败");
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    load();
    return () => {
      ignore = true;
    };
  }, [tripId]);

  const pages = useMemo(() => {
    if (!itinerary) return [];
    return [
      { id: "cover" as const, label: "总览", sub: "行程概要" },
      ...itinerary.days.map((day, index) => ({ id: index, label: `第${day.day}天`, sub: day.date })),
    ];
  }, [itinerary]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-100">
        <p className="text-sm text-slate-500">正在加载输出预览...</p>
      </div>
    );
  }

  if (errorMessage || !itinerary) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-100">
        <div className="rounded-lg border border-red-200 bg-red-50 px-8 py-6 text-center">
          <p className="text-sm text-red-700">{errorMessage || "没有找到行程"}</p>
        </div>
      </div>
    );
  }

  const activeIndex = pages.findIndex((page) => page.id === activePage);

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-100 print:block print:overflow-visible print:bg-white">
      {/* 侧栏与工具条都不进打印 */}
      <div className="hidden w-44 shrink-0 flex-col border-r border-slate-200 bg-white lg:flex print:!hidden">
        <div className="border-b border-slate-100 p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-400">输出方案</p>
          <p className="mt-1 text-xs text-slate-600">共 {pages.length} 页</p>
        </div>
        <div className="flex-1 overflow-auto">
          {pages.map((page) => (
            <button
              key={String(page.id)}
              onClick={() => setActivePage(page.id)}
              className={`w-full border-b border-slate-100 px-4 py-3 text-left transition-colors ${
                activePage === page.id ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <span className="block text-xs font-medium">{page.label}</span>
              <span className={`text-[10px] ${activePage === page.id ? "text-white/60" : "text-slate-400"}`}>
                {page.sub}
              </span>
            </button>
          ))}
        </div>
        <div className="space-y-2 border-t border-slate-100 p-3">
          <button
            onClick={() => window.print()}
            className="w-full rounded bg-slate-900 py-2 text-xs font-medium text-white transition-colors hover:bg-slate-700"
          >
            导出 PDF
          </button>
          <button
            onClick={onBack}
            className="w-full rounded border border-slate-200 py-2 text-xs text-slate-600 transition-colors hover:bg-slate-50"
          >
            ← 返回编辑
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto print:overflow-visible">
        <div className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-2.5 backdrop-blur print:hidden">
          <p className="text-[11px] text-slate-500">只读预览 · 如需修改请返回工作区</p>
          <div className="flex gap-2">
            <button
              onClick={() => setActivePage(pages[Math.max(activeIndex - 1, 0)].id)}
              disabled={activeIndex <= 0}
              className="rounded border border-slate-200 px-3 py-1 text-[11px] text-slate-600 disabled:opacity-40"
            >
              ← 上一页
            </button>
            <button
              onClick={() => setActivePage(pages[Math.min(activeIndex + 1, pages.length - 1)].id)}
              disabled={activeIndex >= pages.length - 1}
              className="rounded border border-slate-200 px-3 py-1 text-[11px] text-slate-600 disabled:opacity-40"
            >
              下一页 →
            </button>
          </div>
        </div>

        {/* print-root：打印时只有这棵子树可见 */}
        <div className="print-root px-6 py-8 print:p-0">
          <CoverSheet itinerary={itinerary} visible={activePage === "cover"} />
          {itinerary.days.map((day, index) => (
            <DaySheet key={day.day} itinerary={itinerary} day={day} visible={activePage === index} />
          ))}
        </div>
      </div>
    </div>
  );
}
