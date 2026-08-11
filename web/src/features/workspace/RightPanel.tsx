import { useState, type ReactNode } from "react";
import { WAnnotation, WBtn } from "../../components/ui/Primitives";
import type { DayPlan, ItineraryItem } from "../../types/itinerary";

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
    .map((item, index) => (item.location ? { item, index, lat: item.location.lat, lng: item.location.lng } : null))
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

export function RightPanel({ day, onOutput }: { day: DayPlan; onOutput: () => void }) {
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
              <span>{key}</span>
              <span className="font-medium text-slate-700">{value}</span>
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
                <span>{key}</span>
                <span>¥ {value}</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-sky-500"
                  style={{ width: `${Math.round((value / budgetTotal) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-2 pt-2 border-t border-slate-200 flex justify-between text-xs font-semibold font-mono text-slate-800">
          <span>合计</span>
          <span>¥ {budgetTotal}</span>
        </div>
      </CollapsibleSection>

      <CollapsibleSection title="数据质量" badge={`${day.items.length} 项`} defaultOpen={false}>
        <div className="space-y-2">
          {dataStats.map(([label, count]) => (
            <div key={label}>
              <div className="mb-1 flex justify-between text-[10px] font-mono text-slate-600">
                <span>{label}</span>
                <span>
                  {count}/{day.items.length}
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${Math.round((count / totalItems) * 100)}%` }}
                />
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
