import { useState, type ReactNode } from "react";
import { WAnnotation, WBtn } from "../../components/ui/Primitives";
import type { DayPlan } from "../../types/itinerary";
import { formatDuration } from "../../types/itinerary";
import { DayMap } from "../../components/ui/DayMap";

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

export function RightPanel({ tripId, day, onOutput }: { tripId: string; day: DayPlan; onOutput: () => void }) {
  const totalTransitMinutes = day.items.reduce((sum, item) => sum + (item.transitMinutes ?? 0), 0);
  const totalStayMinutes = day.items.reduce((sum, item) => sum + item.durationMin, 0);
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
        <DayMap
          tripId={tripId}
          dayNumber={day.day}
          hasCoordinates={day.items.some((item) => item.location)}
          width={480}
          height={320}
          className="h-36 w-full"
        />
        <div className="mt-2 space-y-0.5">
          {/* DayRoute 汇总字段已删除——由条目上的 transitMinutes 直接求和，避免两份数据不一致 */}
          {[
            ["通勤合计", totalTransitMinutes ? `${totalTransitMinutes} 分钟` : "待规划"],
            ["停留合计", formatDuration(totalStayMinutes)],
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

      <CollapsibleSection title="住宿片区" badge={day.stay ? day.city : "未安排"} defaultOpen={false}>
        {day.stay ? (
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-slate-700">{day.stay.area}</p>
            {day.stay.reason && <p className="text-[10px] font-mono text-slate-500">{day.stay.reason}</p>}
          </div>
        ) : (
          <p className="text-[10px] font-mono text-slate-400">当晚无住宿安排（返程日或尚未规划）</p>
        )}
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
