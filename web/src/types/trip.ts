export type ApiTripStatus = "planned" | "completed";
export type TripStatus = "计划中" | "已完成";
export type TripFilter = TripStatus | "全部";
export type TripSort = "updatedAt_desc" | "startDate_desc" | "days_desc";

export type Trip = {
  id: string;
  name: string;
  dest: string;
  days: number;
  date: string;
  status: TripStatus;
  coverUrl?: string;
  updatedAt?: string;
  attractionCount?: number;
};

export type TripListSummary = {
  total: number;
  planned: number;
  completed: number;
  totalDays: number;
  destinationCount: number;
  attractionCount: number;
};

export type TripListResponse = {
  items: Trip[];
  summary: TripListSummary;
};

export type GetTripsParams = {
  status?: ApiTripStatus;
  sort?: TripSort;
  keyword?: string;
};

export type TravelersPayload = {
  adults: number;
  children: number;
  infants: number;
};

export type IntercityTransport = "flight" | "train" | "selfDrive" | "mixed";
export type LocalTransport = "walking" | "transit" | "driving";
export type TravelParty = "solo" | "couple" | "friends" | "family" | "multigenerational";
export type ComfortLevel = "budget" | "standard" | "comfort" | "luxury";
export type ActivityLevel = "low" | "medium" | "high";
export type TripPace = "packed" | "balanced" | "relaxed";
export type VisitHistory = "first" | "returning";

export type CreateTripPayload = {
  originCity: string;
  destination: string;
  startDate: string;
  endDate: string;
  days: number;
  intercityTransport: IntercityTransport;
  travelers: TravelersPayload;
  travelParty: TravelParty;
  visitHistory: VisitHistory;
  preferences: {
    interests: string[];
    pace: TripPace;
    localTransport: LocalTransport[];
    comfortLevel: ComfortLevel;
    activityLevel: ActivityLevel;
    customText: string;
  };
};

/** 枚举值 → 中文标签。表单选项与 LLM prompt 共用同一份，避免两处走样。 */
export const INTERCITY_TRANSPORT_LABELS: Record<IntercityTransport, string> = {
  flight: "飞机",
  train: "高铁 / 火车",
  selfDrive: "自驾",
  mixed: "混合",
};

export const LOCAL_TRANSPORT_LABELS: Record<LocalTransport, string> = {
  walking: "步行为主",
  transit: "公共交通",
  driving: "驾车（自驾·打车·包车）",
};

/** 时间轴展示用的短标签。表单里的 LOCAL_TRANSPORT_LABELS 要说清选项含义，
 *  展示时「驾车（自驾·打车·包车） 20 分钟」过于啰嗦。 */
export const LOCAL_TRANSPORT_SHORT: Record<LocalTransport, string> = {
  walking: "步行",
  transit: "公交",
  driving: "驾车",
};

export const TRAVEL_PARTY_LABELS: Record<TravelParty, string> = {
  solo: "单人",
  couple: "情侣 / 夫妻",
  friends: "朋友同行",
  family: "家庭亲子",
  multigenerational: "多代同游（带老人）",
};

export const COMFORT_LEVEL_LABELS: Record<ComfortLevel, string> = {
  budget: "经济",
  standard: "中等",
  comfort: "舒适",
  luxury: "豪华",
};

export const ACTIVITY_LEVEL_LABELS: Record<ActivityLevel, string> = {
  low: "轻松为主",
  medium: "适度活动",
  high: "能徒步能骑行",
};

export const TRIP_PACE_LABELS: Record<TripPace, string> = {
  relaxed: "慢节奏深度游",
  balanced: "适中",
  packed: "特种兵打卡",
};

export const VISIT_HISTORY_LABELS: Record<VisitHistory, string> = {
  first: "第一次来",
  returning: "来过，想看点不一样的",
};

export type CreateTripResponse = {
  tripId: string;
  jobId: string;
};

export const tripStatusToApi = (status: TripFilter): ApiTripStatus | undefined => {
  if (status === "计划中") return "planned";
  if (status === "已完成") return "completed";
  return undefined;
};
