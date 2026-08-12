import { WImgBox } from "../../components/ui/Primitives";
import type { ItineraryItem } from "../../types/itinerary";
import { STOP_TYPE_LABELS, endTimeOf, formatDuration } from "../../types/itinerary";

export function AttractionCard({
  item,
  onClick,
  onDelete,
  onEdit,
}: {
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
          <span className="rounded-full text-[10px] font-mono text-sky-700 border border-sky-200 bg-sky-50 px-2 py-0.5 shrink-0">
            {STOP_TYPE_LABELS[item.stopType]}
          </span>
        </div>
        <p className="text-xs font-mono text-slate-500 mt-1">
          {item.startTime} - {endTimeOf(item.startTime, item.durationMin)}
        </p>
        {item.address && <p className="mt-1 truncate text-[10px] font-mono text-slate-400">地址 · {item.address}</p>}
        <div className="flex items-center gap-2 mt-2">
          {/* 评分曾是写死的 4.2 + 四颗星。数据模型里没有评分字段，接入真实 POI 评分前不展示。 */}
          <span className="text-[10px] font-mono text-slate-500">
            预计 {formatDuration(item.durationMin)} · {item.cost === 0 ? "免费" : `¥${item.cost}`}
            {item.bookRequired && <span className="ml-1 text-amber-600">· 需预订</span>}
            {item.optional && <span className="ml-1 text-slate-400">· 可选</span>}
          </span>
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
