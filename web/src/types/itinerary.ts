import type { LocalTransport, TravelersPayload } from "./trip";

/** 条目类型。后四种让城际交通与住宿成为时间轴条目，从而参与时间闭合计算。 */
export type StopType = "sight" | "food" | "activity" | "rest" | "flight" | "train" | "transfer" | "hotel";

/** assumption 允许用户纠正，alert 只读。 */
export type NoteKind = "assumption" | "alert";

/** verified = 高德精确匹配；unverified = 匹配可疑，保留名称但不给坐标；
 *  manual = 用户手工添加或改过；placeholder = agent 未接入时的占位条目。 */
export type Verification = "verified" | "unverified" | "manual" | "placeholder";

/** 时段取代精确时刻。
 *
 * 曾由代码累加推算 startTime——起始时刻按节奏拍定，再叠加模型估的停留时长与
 * 高德实测通勤。四个输入里三个是估计，结果却精确到分钟；更糟的是会算出
 * 「14:59 逛夜市」这类语义错误。时段是判断题，交给模型。 */
export type TimeSlot = "dawn" | "morning" | "noon" | "afternoon" | "evening" | "night";

export const TIME_SLOT_LABELS: Record<TimeSlot, string> = {
  dawn: "清晨",
  morning: "上午",
  noon: "中午",
  afternoon: "下午",
  evening: "傍晚",
  night: "晚上",
};

export const STOP_TYPE_LABELS: Record<StopType, string> = {
  sight: "景点",
  food: "餐饮",
  activity: "活动",
  rest: "休息",
  flight: "航班",
  train: "火车",
  transfer: "转移",
  hotel: "住宿",
};

export type ItineraryItem = {
  id: string;
  title: string;
  stopType: StopType;
  timeSlot: TimeSlot;
  /** 分钟数。endTime 与「约 2h」这类展示文本都由它派生，不单独存储。 */
  durationMin: number;
  cost: number;
  optional?: boolean;
  bookRequired?: boolean;
  verification?: Verification;
  reason?: string;
  transitMinutes?: number;
  transitMode?: LocalTransport;
  address?: string;
  location?: { lat: number; lng: number };
  poiId?: string;
  imageUrl?: string;
};

/** 当晚住宿片区。不推荐具体酒店——无法验证空房与价格。city 继承自所属 DayPlan。 */
export type Stay = {
  area: string;
  location?: { lat: number; lng: number };
  reason?: string;
};

export type DayPlan = {
  day: number;
  date: string;
  city: string;
  title: string;
  generationStatus?: "pending" | "generating" | "preview" | "finalized" | "failed";
  weather: { icon: string; desc: string; range: string; tip?: string };
  stay?: Stay | null;
  items: ItineraryItem[];
};

export type PlanNote = {
  kind: NoteKind;
  text: string;
};

export type Itinerary = {
  tripId: string;
  title: string;
  dateRange: string;
  originCity: string;
  /** route 是有序途经城市；destination 是它的展示摘要。 */
  destination: string;
  route: string[];
  travelers: TravelersPayload;
  interests: string[];
  notes: PlanNote[];
  days: DayPlan[];
};

/** 分钟数 → 展示文本。取代原先存库的 durationLabel。 */
export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h && m) return `${h}h${m}m`;
  if (h) return `${h}h`;
  return `${m}m`;
}
