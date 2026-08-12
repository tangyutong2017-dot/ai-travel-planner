import type { StopType } from "../../types/itinerary";
import { STOP_TYPE_LABELS } from "../../types/itinerary";

/** 按类型区分的图标与配色。
 *
 * 用图标而非「假照片」：拿不到真实图片时，一张风景占位图会让人误以为那是该地点的照片。
 * 图标明确表示「这里没有照片」，同时仍然传达条目类型。
 */
const STOP_THUMB_STYLES: Record<StopType, { icon: string; className: string }> = {
  sight: { icon: "🏞", className: "bg-sky-50 border-sky-100 text-sky-600" },
  food: { icon: "🍜", className: "bg-orange-50 border-orange-100 text-orange-600" },
  activity: { icon: "🎯", className: "bg-emerald-50 border-emerald-100 text-emerald-600" },
  rest: { icon: "☕", className: "bg-amber-50 border-amber-100 text-amber-600" },
  flight: { icon: "✈", className: "bg-indigo-50 border-indigo-100 text-indigo-600" },
  train: { icon: "🚄", className: "bg-indigo-50 border-indigo-100 text-indigo-600" },
  transfer: { icon: "🚕", className: "bg-slate-100 border-slate-200 text-slate-500" },
  hotel: { icon: "🏨", className: "bg-violet-50 border-violet-100 text-violet-600" },
};

export function StopThumb({
  stopType,
  className = "",
  showLabel = true,
}: {
  stopType: StopType;
  className?: string;
  showLabel?: boolean;
}) {
  const { icon, className: tone } = STOP_THUMB_STYLES[stopType];

  return (
    <div className={`flex flex-col items-center justify-center gap-0.5 rounded-md border ${tone} ${className}`}>
      <span className="leading-none">{icon}</span>
      {showLabel && <span className="text-[9px] font-mono leading-none">{STOP_TYPE_LABELS[stopType]}</span>}
    </div>
  );
}
