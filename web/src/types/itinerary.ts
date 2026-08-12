import type { LocalTransport, TravelersPayload } from "./trip";

/** 条目类型。后四种让城际交通与住宿成为时间轴条目，从而参与时间闭合计算。 */
export type StopType = "sight" | "food" | "activity" | "rest" | "flight" | "train" | "transfer" | "hotel";

export type Intensity = "low" | "mid" | "high";
export type BookingUrgency = "high" | "mid" | "low";

/** assumption 允许用户纠正，alert 只读。 */
export type NoteKind = "assumption" | "alert";

/** verified = 高德精确匹配；unverified = 匹配可疑，保留名称但不给坐标；
 *  manual = 用户手工添加或改过；placeholder = agent 未接入时的占位条目。 */
export type Verification = "verified" | "unverified" | "manual" | "placeholder";

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
  startTime: string;
  /** 分钟数。endTime 与「约 2h」这类展示文本都由它派生，不单独存储。 */
  durationMin: number;
  cost: number;
  optional?: boolean;
  intensity?: Intensity;
  bookRequired?: boolean;
  verification?: Verification;
  reason?: string;
  transitMinutes?: number;
  transitMode?: LocalTransport;
  address?: string;
  location?: { lat: number; lng: number };
  poiId?: string;
  imageUrl?: string;
  mealType?: string;
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

/** 预订待办。名称从 itemId 指向的条目取，不重复存储。 */
export type Booking = {
  itemId: string;
  channel: string;
  leadTimeDays?: number;
  urgency?: BookingUrgency;
  note?: string;
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
  bookings: Booking[];
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

/** startTime + durationMin → 结束时刻。取代原先存库的 endTime。 */
export function endTimeOf(startTime: string, durationMin: number): string {
  const [h, m] = startTime.split(":").map(Number);
  if (Number.isNaN(h) || Number.isNaN(m)) return startTime;
  const total = h * 60 + m + durationMin;
  const hh = Math.floor(total / 60) % 24;
  return `${String(hh).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}
