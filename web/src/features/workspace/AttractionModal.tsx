import { Divider, WAnnotation, WBtn, WImgBox } from "../../components/ui/Primitives";
import type { ItineraryItem } from "../../types/itinerary";
import { STOP_TYPE_LABELS, endTimeOf, formatDuration } from "../../types/itinerary";

export function ModalAttraction({ item, onClose }: { item: ItineraryItem; onClose: () => void }) {
  const VERIFICATION_LABELS: Record<string, string> = {
    verified: "高德已核实",
    unverified: "未核实",
    manual: "手动添加",
    placeholder: "占位数据",
  };

  const detailRows = [
    ["游览时间", `${item.startTime} - ${endTimeOf(item.startTime, item.durationMin)}`],
    ["建议停留", formatDuration(item.durationMin)],
    ["费用", item.cost === 0 ? "免费" : `¥${item.cost}`],
    ["地址", item.address || "暂无地址"],
    ["上一站交通", item.transitMinutes ? `${item.transitMinutes} 分钟` : "首站 / 暂无"],
    ["坐标", item.location ? `${item.location.lat}, ${item.location.lng}` : "暂无坐标"],
    ["核实状态", VERIFICATION_LABELS[item.verification ?? "unverified"]],
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
              <img
                className="h-36 w-52 shrink-0 rounded-lg object-cover"
                src={item.imageUrl}
                alt={`${item.title} 主图`}
              />
            ) : (
              <WImgBox className="w-52 h-36 shrink-0 rounded-lg" label="景点主图" />
            )}
            <div className="flex-1">
              <div className="flex flex-wrap gap-1.5 mb-3">
                {[
                  STOP_TYPE_LABELS[item.stopType],
                  VERIFICATION_LABELS[item.verification ?? "unverified"],
                  item.poiId ? "POI" : "未匹配POI",
                ].map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-mono text-slate-600"
                  >
                    {tag}
                  </span>
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
            <WBtn
              label="复制位置"
              small
              onClick={() => {
                if (item.location) void navigator.clipboard?.writeText(`${item.location.lat},${item.location.lng}`);
              }}
            />
            <WBtn label="✓ 已在行程中" primary small />
          </div>
        </div>
      </div>
    </div>
  );
}
