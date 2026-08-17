import { useState } from "react";
import { API_BASE_URL } from "../../api/client";

/** 当日动线地图。
 *
 * 图由后端代理高德静态地图生成——走后端是为了让高德 key 留在服务端。
 * 选静态图而非 JS SDK：输出页要打印成 PDF，交互式地图打印不出来；
 * 工作区右栏那块本来也只是缩略预览。
 *
 * 没有已核实坐标、或图片加载失败时退回占位块，不画一张空地图冒充。
 */
export function DayMap({
  tripId,
  dayNumber,
  hasCoordinates,
  width,
  height,
  className = "",
}: {
  tripId: string;
  dayNumber: number;
  hasCoordinates: boolean;
  width: number;
  height: number;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);

  if (!hasCoordinates || failed) {
    return (
      <div
        className={`flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 text-center ${className}`}
      >
        <span className="text-[11px] font-medium text-slate-500">暂无地图</span>
        <span className="mt-1 text-[10px] font-mono text-slate-400">
          {hasCoordinates ? "地图服务暂时不可用" : "地点核实后显示动线"}
        </span>
      </div>
    );
  }

  return (
    <img
      src={`${API_BASE_URL}/api/trips/${tripId}/days/${dayNumber}/map.png?width=${width}&height=${height}`}
      alt={`第 ${dayNumber} 天动线地图`}
      loading="lazy"
      onError={() => setFailed(true)}
      className={`rounded-lg border border-slate-200 object-cover ${className}`}
    />
  );
}
