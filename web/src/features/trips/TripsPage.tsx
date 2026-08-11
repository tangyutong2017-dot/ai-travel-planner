import { useEffect, useState } from "react";
import { deleteTrip, getTrips, updateTripName } from "../../api/trips";
import type { Trip, TripFilter, TripListResponse, TripSort, TripStatus } from "../../types/trip";
import { tripStatusToApi } from "../../types/trip";
import { Divider, WAnnotation, WBox, WBtn, WImgBox } from "../../components/ui/Primitives";

function EmptyTrips({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-slate-50 px-6">
      {/* 插图占位 */}
      <div className="w-64 h-44 rounded-2xl bg-white border border-slate-200 shadow-sm shadow-slate-200/70 flex flex-col items-center justify-center gap-3 mb-8 relative overflow-hidden">
        {/* 装饰性线条模拟地图感 */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-6 left-8 right-8 h-px bg-gray-600" />
          <div className="absolute top-12 left-12 right-12 h-px bg-gray-600" />
          <div className="absolute top-18 left-6 right-20 h-px bg-gray-600" />
          <div className="absolute bottom-10 left-10 right-6 h-px bg-gray-600" />
          <div className="absolute bottom-6 left-16 right-10 h-px bg-gray-600" />
          <div className="absolute top-4 bottom-4 left-10 w-px bg-gray-600" />
          <div className="absolute top-8 bottom-8 right-16 w-px bg-gray-600" />
          {/* 地图图钉 */}
          <div className="absolute top-8 left-16 w-3 h-3 border-2 border-gray-700 rounded-full bg-white" />
          <div className="absolute top-16 right-14 w-3 h-3 border-2 border-gray-700 rounded-full bg-white" />
          <div className="absolute bottom-12 left-20 w-3 h-3 border-2 border-gray-700 rounded-full bg-white" />
        </div>
        {/* 主图标 */}
        <div className="w-14 h-14 rounded-2xl border-2 border-dashed border-sky-300 flex items-center justify-center bg-sky-50 z-10">
          <span className="text-2xl">✈</span>
        </div>
        <span className="text-xs font-mono text-slate-400 z-10">插图占位</span>
      </div>

      {/* 文案 */}
      <h2 className="text-xl font-bold text-slate-900 mb-2 text-center">还没有行程，出发规划吧</h2>
      <p className="text-sm text-slate-500 font-mono text-center max-w-xs leading-relaxed mb-8">
        告诉 AI 你想去哪、几天、和谁去，<br />几秒内生成专属行程方案
      </p>

      {/* 主 CTA */}
      <button
        onClick={onCreate}
        className="rounded-lg bg-sky-600 text-white text-sm font-semibold px-8 py-3 cursor-pointer hover:bg-sky-700 transition-colors mb-4 shadow-sm shadow-sky-200"
      >
        + 创建我的第一个行程
      </button>

      {/* 次要操作 */}
      <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
        <button className="hover:text-slate-700 cursor-pointer transition-colors underline underline-offset-2">
          浏览热门行程模板
        </button>
        <span>·</span>
        <button className="hover:text-slate-700 cursor-pointer transition-colors underline underline-offset-2">
          导入已有行程
        </button>
      </div>

      {/* 功能亮点提示 */}
      <div className="mt-12 grid grid-cols-3 gap-6 max-w-lg">
        {[
          { icon: "◈", title: "个性化偏好", desc: "根据兴趣、节奏、预算智能推荐" },
          { icon: "▦", title: "可视化编辑", desc: "拖拽调整景点，实时预览路线" },
          { icon: "⬡", title: "一键导出", desc: "PDF、日历、分享链接多格式输出" },
        ].map((f) => (
          <div key={f.title} className="text-center">
            <div className="w-8 h-8 rounded-lg border border-slate-200 bg-white flex items-center justify-center mx-auto mb-2 text-sky-600">
              {f.icon}
            </div>
            <p className="text-xs font-semibold text-slate-700 mb-1">{f.title}</p>
            <p className="text-[11px] font-mono text-slate-400 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TripsNoResults({
  keyword,
  filter,
  onClear,
  onCreate,
}: {
  keyword: string;
  filter: TripFilter;
  onClear: () => void;
  onCreate: () => void;
}) {
  const hasCondition = Boolean(keyword) || filter !== "全部";
  const title = hasCondition ? "没有匹配的行程" : "还没有行程，出发规划吧";
  const description = hasCondition
    ? "可以清空搜索和筛选条件，或者直接创建一个新的旅行计划。"
    : "告诉 AI 你想去哪、几天、和谁去，快速生成专属行程方案。";

  return (
    <div className="col-span-3 rounded-2xl border border-dashed border-sky-200 bg-white px-6 py-10 text-center shadow-sm shadow-slate-200/50">
      <div className="relative mx-auto mb-5 flex h-28 w-44 items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute left-5 right-5 top-7 h-px bg-slate-700" />
          <div className="absolute left-8 right-8 top-14 h-px bg-slate-700" />
          <div className="absolute bottom-7 left-6 right-6 h-px bg-slate-700" />
          <div className="absolute bottom-4 top-4 left-10 w-px bg-slate-700" />
          <div className="absolute bottom-6 top-6 right-12 w-px bg-slate-700" />
        </div>
        <div className="z-10 flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-dashed border-sky-300 bg-sky-50 text-2xl text-sky-500">
          +
        </div>
      </div>
      <h2 className="text-base font-bold text-slate-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-slate-500">{description}</p>
      {hasCondition && (
        <p className="mt-2 text-[10px] font-mono text-slate-400">
          当前条件：{keyword ? `关键词「${keyword}」` : ""}{keyword && filter !== "全部" ? " · " : ""}{filter !== "全部" ? filter : ""}
        </p>
      )}
      <div className="mt-5 flex justify-center gap-2">
        {hasCondition && (
          <button
            onClick={onClear}
            className="rounded-md border border-slate-200 bg-white px-4 py-2 text-xs font-mono text-slate-600 transition-colors hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700"
          >
            清空条件
          </button>
        )}
        <button
          onClick={onCreate}
          className="rounded-md border border-sky-600 bg-sky-600 px-4 py-2 text-xs font-semibold text-white shadow-sm shadow-sky-200 transition-colors hover:bg-sky-700"
        >
          + 创建新行程
        </button>
      </div>
    </div>
  );
}

const landmarkCoverUrls: Array<[string, string]> = [
  ["西藏", "https://commons.wikimedia.org/wiki/Special:FilePath/Potala%20Palace%2C%20Lhasa%2C%20Tibet.jpg"],
  ["拉萨", "https://commons.wikimedia.org/wiki/Special:FilePath/Potala%20Palace%2C%20Lhasa%2C%20Tibet.jpg"],
  ["云南大理", "https://commons.wikimedia.org/wiki/Special:FilePath/Dali%20old%20town%2C%20Yunnan%2C%20China.jpg"],
  ["大理", "https://commons.wikimedia.org/wiki/Special:FilePath/Dali%20old%20town%2C%20Yunnan%2C%20China.jpg"],
  ["北京", "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?auto=format&fit=crop&w=1200&q=80"],
  ["浙江杭州", "https://commons.wikimedia.org/wiki/Special:FilePath/West%20Lake%2C%20Hangzhou.jpg"],
  ["杭州", "https://commons.wikimedia.org/wiki/Special:FilePath/West%20Lake%2C%20Hangzhou.jpg"],
  ["四川成都", "https://commons.wikimedia.org/wiki/Special:FilePath/Anshun%20Bridge%20in%20Chengdu.jpg"],
  ["成都", "https://commons.wikimedia.org/wiki/Special:FilePath/Anshun%20Bridge%20in%20Chengdu.jpg"],
  ["上海", "https://commons.wikimedia.org/wiki/Special:FilePath/Shanghai%20skyline%202018%28cropped%29.jpg"],
  ["广西桂林", "https://commons.wikimedia.org/wiki/Special:FilePath/Guilin%20Li%20River.jpg"],
  ["桂林", "https://commons.wikimedia.org/wiki/Special:FilePath/Guilin%20Li%20River.jpg"],
];

function fallbackCoverUrl(destination: string) {
  return landmarkCoverUrls.find(([keyword]) => destination.includes(keyword) || keyword.includes(destination))?.[1] ?? null;
}

export function PageMyTrips({
  onCreate,
  onOpenTrip,
  onTripsChanged,
}: {
  onCreate: () => void;
  onOpenTrip: (tripId: string) => void;
  onTripsChanged: () => void;
}) {
  const [isEmpty, setIsEmpty] = useState(false);
  const [activeFilter, setActiveFilter] = useState<TripFilter>("全部");
  const [sortMode, setSortMode] = useState<TripSort>("updatedAt_desc");
  const [searchText, setSearchText] = useState("");
  const [debouncedSearchText, setDebouncedSearchText] = useState("");
  const [tripData, setTripData] = useState<TripListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [deletingTripId, setDeletingTripId] = useState<string | null>(null);
  const [openMenuTripId, setOpenMenuTripId] = useState<string | null>(null);
  const [renamingTrip, setRenamingTrip] = useState<Trip | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [isRenaming, setIsRenaming] = useState(false);

  const statusColors: Record<TripStatus, string> = {
    "计划中": "border-sky-200 bg-sky-50 text-sky-700",
    "已完成": "border-emerald-300 bg-emerald-50 text-emerald-700",
  };

  const filterColors: Record<TripFilter, string> = {
    "全部": "bg-slate-900 text-white border-slate-900",
    "计划中": "bg-sky-600 text-white border-sky-600",
    "已完成": "bg-emerald-600 text-white border-emerald-600",
  };

  const sortLabels: Record<TripSort, string> = {
    updatedAt_desc: "最近修改",
    startDate_desc: "出发日期",
    days_desc: "行程天数",
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearchText(searchText.trim());
    }, 250);

    return () => window.clearTimeout(timer);
  }, [searchText]);

  useEffect(() => {
    let ignore = false;

    async function loadTrips() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const data = await getTrips({
          status: tripStatusToApi(activeFilter),
          sort: sortMode,
          keyword: debouncedSearchText || undefined,
        });

        if (!ignore) {
          setTripData(data);
        }
      } catch (error) {
        if (!ignore) {
          setErrorMessage(error instanceof Error ? error.message : "行程加载失败");
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    loadTrips();

    return () => {
      ignore = true;
    };
  }, [activeFilter, debouncedSearchText, reloadKey, sortMode]);

  const visibleTrips = tripData?.items ?? [];
  const handleDeleteTrip = async (trip: Trip) => {
    const confirmed = window.confirm(`确定删除「${trip.name}」吗？相关行程详情和生成任务也会一起删除。`);
    if (!confirmed) return;

    setDeletingTripId(trip.id);
    setErrorMessage("");

    try {
      await deleteTrip(trip.id);
      const freshTrips = await getTrips({
        status: tripStatusToApi(activeFilter),
        sort: sortMode,
        keyword: debouncedSearchText || undefined,
      });
      setTripData(freshTrips);
      setOpenMenuTripId(null);
      setReloadKey((key) => key + 1);
      onTripsChanged();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "删除行程失败");
    } finally {
      setDeletingTripId(null);
    }
  };

  const openRenameTrip = (trip: Trip) => {
    setOpenMenuTripId(null);
    setRenamingTrip(trip);
    setRenameValue(trip.name);
  };

  const handleRenameTrip = async () => {
    if (!renamingTrip || !renameValue.trim() || isRenaming) return;

    setIsRenaming(true);
    setErrorMessage("");

    try {
      await updateTripName(renamingTrip.id, renameValue.trim());
      setRenamingTrip(null);
      setRenameValue("");
      setReloadKey((key) => key + 1);
      onTripsChanged();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "重命名失败");
    } finally {
      setIsRenaming(false);
    }
  };

  const clearSearchConditions = () => {
    setSearchText("");
    setDebouncedSearchText("");
    setActiveFilter("全部");
  };

  if (isEmpty) {
    return (
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶栏保留，含切换开关 */}
        <div className="border-b border-slate-200 bg-white px-6 py-3 flex items-center justify-between shrink-0">
          <h1 className="text-sm font-semibold text-slate-800">我的行程</h1>
          <button
            onClick={() => setIsEmpty(false)}
            className="rounded-md text-[11px] font-mono text-slate-400 border border-dashed border-slate-300 px-3 py-1 cursor-pointer hover:border-slate-500 hover:text-slate-600 transition-colors"
          >
            预览：有行程状态 →
          </button>
        </div>
        <EmptyTrips onCreate={onCreate} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto bg-slate-50">
      <div className="max-w-6xl mx-auto py-8 px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm shadow-slate-200/60 backdrop-blur">
          <div>
            <WAnnotation text="Trips dashboard" />
            <h1 className="text-[22px] font-bold text-slate-950 mt-1">我的行程</h1>
            <p className="text-[13px] text-slate-500 mt-1">管理计划中的旅程，查看已完成的路线和预算概览。</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsEmpty(true)}
              className="rounded-md text-[11px] font-mono text-slate-400 border border-dashed border-slate-300 px-3 py-1.5 cursor-pointer hover:border-slate-500 hover:text-slate-600 transition-colors"
            >
              ← 预览：空状态
            </button>
            <WBtn label="+ 创建新行程" primary onClick={onCreate} />
          </div>
        </div>

        {/* Filter / sort bar */}
        <div className="flex items-center gap-3 mb-5 rounded-xl border border-slate-200/80 bg-white/85 p-3 shadow-sm shadow-slate-200/50 backdrop-blur">
          <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
            {(["全部", "计划中", "已完成"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={`rounded-md text-[11px] font-mono px-3 py-1.5 border cursor-pointer transition-all ${
                  activeFilter === f ? filterColors[f] : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          <div className="flex-1" />
          <WAnnotation text="状态筛选" />
          <WAnnotation text="排序：" />
          <label className="relative">
            <select
              value={sortMode}
              onChange={(event) => setSortMode(event.target.value as TripSort)}
              className="h-9 appearance-none rounded-md border border-slate-200 bg-white pl-3 pr-8 text-xs font-mono text-slate-600 outline-none transition-colors hover:border-sky-200 focus:border-sky-400"
            >
              {Object.entries(sortLabels).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-slate-400">▾</span>
          </label>
          <label className="flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2 transition-colors focus-within:border-sky-400">
            <span className="text-xs font-mono text-slate-500">🔍</span>
            <input
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="搜索行程"
              className="w-32 bg-transparent text-xs font-mono text-slate-600 outline-none placeholder:text-slate-400"
            />
            {searchText && (
              <button
                onClick={() => setSearchText("")}
                className="rounded px-1 text-[10px] font-mono text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                type="button"
              >
                ×
              </button>
            )}
          </label>
        </div>

        {/* Trip cards grid */}
        <div className="grid grid-cols-3 gap-5">
          {isLoading && (
            <div className="col-span-3 rounded-xl border border-slate-200 bg-white py-12 text-center shadow-sm">
              <p className="text-sm font-medium text-slate-700">正在加载行程...</p>
              <p className="text-xs font-mono text-slate-400 mt-1">正在同步你的旅行数据</p>
            </div>
          )}

          {!isLoading && errorMessage && (
            <div className="col-span-3 border border-red-200 bg-red-50 py-12 text-center">
              <p className="text-sm font-medium text-red-700">{errorMessage}</p>
              <button
                onClick={() => setReloadKey((key) => key + 1)}
                className="mt-3 border border-red-300 bg-white px-3 py-1.5 text-xs font-mono text-red-700"
              >
                重试
              </button>
            </div>
          )}

          {!isLoading && !errorMessage && visibleTrips.map((t: Trip) => (
            (() => {
              const coverUrl = t.coverUrl ?? fallbackCoverUrl(t.dest);

              return (
                <WBox
                  key={t.name}
                  className="group cursor-pointer overflow-hidden hover:border-sky-200 hover:shadow-lg hover:shadow-sky-100/70 transition-all ring-1 ring-transparent hover:ring-sky-200/60"
                  onClick={() => onOpenTrip(t.id)}
                >
                  {coverUrl ? (
                    <div className="relative h-36 w-full overflow-hidden">
                      <img className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" src={coverUrl} alt={`${t.name} 封面`} />
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/35 via-transparent to-white/5" />
                      <div className="absolute left-3 bottom-3 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-mono text-slate-700 shadow-sm">
                        {t.dest}
                      </div>
                    </div>
                  ) : (
                    <WImgBox className="w-full h-36" label={`封面 · ${t.dest}`} />
                  )}
                  <div className="p-4">
                <div className="flex items-start justify-between gap-1 mb-1">
                  <p className="text-[15px] font-semibold text-slate-900 leading-tight group-hover:text-sky-700 transition-colors">{t.name}</p>
                  <span className={`rounded-full text-[10px] font-mono border px-2 py-0.5 shrink-0 ${statusColors[t.status]}`}>
                    {t.status}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500 mb-3">
                  <span>📍 {t.dest}</span>
                  <span>📅 {t.days}天</span>
                </div>
                <p className="text-[10px] font-mono text-slate-400 mb-3">出行日期 · {t.date}</p>
                <Divider className="mb-2" />
                <div className="flex gap-1.5">
                  <WBtn label="继续编辑" small className="min-w-0 flex-1 text-center" onClick={() => onOpenTrip(t.id)} />
                  <button
                    onClick={(event) => event.stopPropagation()}
                    className="rounded-md border border-slate-200 bg-white px-3 py-1 text-[11px] font-mono text-slate-700 transition-all hover:-translate-y-px hover:border-sky-200 hover:bg-sky-50"
                  >
                    分享
                  </button>
                  <div className="relative">
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        setOpenMenuTripId((current) => (current === t.id ? null : t.id));
                      }}
                      className="rounded-md border border-slate-200 bg-white px-3 py-1 text-[11px] font-mono text-slate-700 transition-all hover:-translate-y-px hover:border-sky-200 hover:bg-sky-50"
                      aria-label={`${t.name} 更多操作`}
                    >
                      ···
                    </button>
                    {openMenuTripId === t.id && (
                      <div
                        className="absolute bottom-8 right-0 z-20 w-32 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg shadow-slate-200/70"
                        onClick={(event) => event.stopPropagation()}
                      >
                        <button
                          onClick={() => openRenameTrip(t)}
                          className="block w-full px-3 py-2 text-left text-[11px] font-mono text-slate-600 transition-colors hover:bg-sky-50 hover:text-sky-700"
                        >
                          重命名
                        </button>
                        <button
                          onClick={() => void handleDeleteTrip(t)}
                          disabled={deletingTripId === t.id}
                          className="block w-full px-3 py-2 text-left text-[11px] font-mono text-red-600 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {deletingTripId === t.id ? "删除中" : "删除"}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                  </div>
                </WBox>
              );
            })()
          ))}

          {!isLoading && !errorMessage && visibleTrips.length === 0 && (
            <TripsNoResults
              keyword={debouncedSearchText}
              filter={activeFilter}
              onClear={clearSearchConditions}
              onCreate={onCreate}
            />
          )}

          {/* New trip card */}
          <div
            className="rounded-lg border border-dashed border-sky-300 bg-white flex flex-col items-center justify-center min-h-56 cursor-pointer hover:bg-sky-50 transition-colors"
            onClick={onCreate}
          >
            <div className="w-10 h-10 rounded-xl border-2 border-dashed border-sky-300 flex items-center justify-center text-2xl text-sky-500 mb-2">+</div>
            <p className="text-sm font-medium text-slate-600">创建新行程</p>
            <p className="text-xs font-mono text-slate-400 mt-1">AI 帮你规划</p>
          </div>
        </div>

        {renamingTrip && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35">
            <div className="w-[420px] rounded-xl border border-slate-200 bg-white shadow-2xl shadow-slate-950/20">
              <div className="border-b border-slate-100 px-5 py-3">
                <WAnnotation text="Trip name" />
                <h2 className="text-sm font-semibold text-slate-900">重命名行程</h2>
              </div>
              <div className="p-5">
                <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
                  行程名称
                  <input
                    value={renameValue}
                    onChange={(event) => setRenameValue(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") void handleRenameTrip();
                    }}
                    className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-sky-400"
                    autoFocus
                  />
                </label>
                <p className="mt-2 text-[10px] font-mono text-slate-400">名称会同步到工作区和输出预览。</p>
              </div>
              <div className="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">
                <WBtn label="取消" small onClick={() => setRenamingTrip(null)} />
                <WBtn label={isRenaming ? "保存中" : "保存"} small primary onClick={() => void handleRenameTrip()} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
