import { WImgBox } from "../ui/Primitives";
import type { Trip } from "../../types/trip";

export function TopNav({ title }: { title: string }) {
  return (
    <div className="border-b border-slate-200/80 bg-white/85 backdrop-blur-xl flex items-stretch h-13 shrink-0 shadow-sm shadow-slate-200/40">
      {/* Logo */}
      <div className="border-r border-slate-100 px-5 flex items-center gap-3 shrink-0 w-56">
        <div className="w-7 h-7 rounded-lg bg-slate-950 text-sky-200 flex items-center justify-center text-[12px] font-bold shadow-sm shadow-sky-200 ring-1 ring-sky-400/20">
          AI
        </div>
        <div>
          <span className="block font-semibold text-[13px] tracking-tight text-slate-900">AI 行程规划</span>
          <span className="block text-[10px] font-mono text-slate-400">Travel Planner</span>
        </div>
      </div>
      {/* Center: breadcrumb / page title */}
      <div className="flex items-center px-5 flex-1">
        <span className="text-xs font-mono text-slate-400">{title}</span>
      </div>
      {/* Right: actions + user */}
      <div className="border-l border-slate-100 px-4 flex items-center gap-3 shrink-0">
        <button className="rounded-md text-[11px] font-mono text-slate-500 border border-slate-200 px-3 py-1.5 hover:bg-sky-50 hover:border-sky-200 cursor-pointer">
          🔔
        </button>
        <button className="rounded-md text-[11px] font-mono text-slate-500 border border-slate-200 px-3 py-1.5 hover:bg-sky-50 hover:border-sky-200 cursor-pointer">
          设置
        </button>
        <div className="flex items-center gap-2">
          <WImgBox className="w-8 h-8 rounded-full" label="" />
          <span className="text-[11px] font-mono text-slate-600">用户名</span>
        </div>
      </div>
    </div>
  );
}

// ─── LeftSidebar ────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: "mytrips", icon: "⊞", label: "我的行程" },
  { id: "workspace", icon: "▦", label: "行程工作区" },
  { id: "output", icon: "⬡", label: "输出预览" },
];

export function LeftSidebar({
  current,
  onNavigate,
  onCreateTrip,
  recentTrips,
  onOpenTrip,
}: {
  current: string;
  onNavigate: (id: string) => void;
  onCreateTrip: () => void;
  recentTrips: Trip[];
  onOpenTrip: (tripId: string) => void;
}) {
  return (
    <div className="w-56 border-r border-slate-200 bg-white/80 backdrop-blur-xl flex flex-col shrink-0 overflow-y-auto print:hidden">
      {/* Create trip CTA */}
      <div className="p-4 border-b border-slate-100">
        <button
          onClick={onCreateTrip}
          className="w-full rounded-lg bg-slate-950 text-sky-100 text-[11px] font-mono font-semibold py-2.5 flex items-center justify-center gap-2 cursor-pointer hover:bg-slate-800 transition-all shadow-sm shadow-sky-200 ring-1 ring-sky-400/20"
        >
          <span className="text-base leading-none">+</span>
          创建新行程
        </button>
      </div>

      {/* Main nav */}
      <div className="flex-1 py-3">
        <p className="text-[10px] font-mono text-slate-400 uppercase tracking-widest px-4 mb-2">导航</p>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-2.5 text-[11px] font-mono cursor-pointer transition-colors text-left ${
              current === item.id
                ? "bg-sky-50 text-sky-700 border-r-2 border-sky-500"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
            }`}
          >
            <span className="text-sm leading-none w-4 text-center">{item.icon}</span>
            <span>{item.label}</span>
            {current === item.id && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-sky-500" />}
          </button>
        ))}
      </div>

      {/* Recent trips */}
      <div className="border-t border-slate-100 p-4">
        <p className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-2">最近行程</p>
        {recentTrips.slice(0, 3).map((trip) => (
          <button
            key={trip.id}
            onClick={() => onOpenTrip(trip.id)}
            className="w-full text-left flex items-center gap-2 py-1.5 text-xs font-mono text-slate-500 hover:text-slate-900 cursor-pointer transition-colors"
          >
            <span className="w-1.5 h-1.5 bg-sky-400 rounded-full shrink-0" />
            <span className="flex-1 truncate">
              {trip.dest} {trip.days}日
            </span>
            <span className={`text-[10px] ${trip.status === "计划中" ? "text-sky-300" : "text-emerald-400"}`}>
              {trip.status}
            </span>
          </button>
        ))}
        {recentTrips.length === 0 && (
          <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 px-2 py-2 text-[10px] font-mono text-slate-400">
            暂无最近行程
          </div>
        )}
      </div>

      {/* Bottom */}
      <div className="border-t border-slate-100 p-4 space-y-1">
        {["帮助中心", "意见反馈"].map((label) => (
          <button
            key={label}
            className="w-full text-left text-xs font-mono text-slate-400 hover:text-slate-700 py-1 cursor-pointer transition-colors"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
