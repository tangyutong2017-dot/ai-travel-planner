from typing import Literal

from pydantic import BaseModel, Field, model_validator


TripStatus = Literal["planned", "completed"]
AgentJobStatus = Literal["queued", "running", "succeeded", "failed"]
DayGenerationStatus = Literal["pending", "generating", "preview", "finalized", "failed"]


class Travelers(BaseModel):
    adults: int = Field(ge=0)
    children: int = Field(ge=0)
    infants: int = Field(ge=0)

    @property
    def total(self) -> int:
        return self.adults + self.children + self.infants

    @model_validator(mode="after")
    def require_at_least_one_traveler(self) -> "Travelers":
        if self.total <= 0:
            raise ValueError("At least one traveler is required")

        return self


# 城际交通：怎么来、怎么走，决定首末日的可用时间
IntercityTransport = Literal["flight", "train", "selfDrive", "mixed"]

# 市内通勤：只保留三种，因为路线计算只有这三种走法。
# 自驾 / 打车 / 包车在路线计算上完全等价，拆开会让用户在无差别的选项间做选择。
LocalTransport = Literal["walking", "transit", "driving"]

# 同行关系。人数给精确值，这里给语义——同样 2 个成人，情侣和朋友的行程不同
TravelParty = Literal["solo", "couple", "friends", "family", "multigenerational"]

# 档次偏好。取代原先的住宿类型：它同时影响餐饮与住宿片区，且不需要任何价格数据源
ComfortLevel = Literal["budget", "standard", "comfort", "luxury"]

# 体力接受度。带老人或体力弱时，长距离徒步是硬约束而非偏好
ActivityLevel = Literal["low", "medium", "high"]

# 节奏。原为 1-100 数值，但代码本就压成三档，且已决定交给 LLM 理解语义
TripPace = Literal["packed", "balanced", "relaxed"]

# 是否来过。二刷需要避开首刷已打卡的热门点
VisitHistory = Literal["first", "returning"]


class TripPreferences(BaseModel):
    interests: list[str]
    pace: TripPace
    localTransport: list[LocalTransport]
    comfortLevel: ComfortLevel
    activityLevel: ActivityLevel
    customText: str = ""


class CreateTripPayload(BaseModel):
    originCity: str
    destination: str
    startDate: str
    endDate: str
    days: int = Field(ge=1, le=60)
    intercityTransport: IntercityTransport
    travelers: Travelers
    travelParty: TravelParty
    visitHistory: VisitHistory
    preferences: TripPreferences


class CreateTripResponse(BaseModel):
    tripId: str


class GenerateTripResponse(BaseModel):
    tripId: str
    jobId: str


class Trip(BaseModel):
    id: str
    name: str
    dest: str
    days: int
    date: str
    status: TripStatus
    coverUrl: str | None = None
    updatedAt: str | None = None
    attractionCount: int | None = None


class UpdateTripPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class TripListSummary(BaseModel):
    total: int
    planned: int
    completed: int
    totalDays: int
    destinationCount: int
    attractionCount: int


class TripListResponse(BaseModel):
    items: list[Trip]
    summary: TripListSummary


# 条目类型。取代原先的自由字符串 type——枚举才能让 UI 决定图标、让校验器区分条目。
# 后四种让城际交通与住宿成为时间轴上的条目，从而参与时间闭合计算。
StopType = Literal["sight", "food", "activity", "rest", "flight", "train", "transfer", "hotel"]

# 体力强度。与输入侧的 activityLevel 配对，低体力用户不应排入 high 项。
Intensity = Literal["low", "mid", "high"]

BookingUrgency = Literal["high", "mid", "low"]

# AI 说明。assumption 允许用户纠正，alert 只读。
NoteKind = Literal["assumption", "alert"]

# 印证状态。verified = 高德精确匹配；unverified = 匹配可疑，保留名称但不给坐标；
# manual = 用户手工添加或改过；placeholder = agent 未接入时的占位条目。
Verification = Literal["verified", "unverified", "manual", "placeholder"]


class ItineraryItem(BaseModel):
    id: str
    title: str
    stopType: StopType
    startTime: str
    # 时长与通勤都存分钟数：校验器无法从 "2h" / "地铁 15 分钟" 这类展示文本算时间闭合。
    # endTime 与 durationLabel 均可由此派生，不再单独存储。
    durationMin: int = Field(ge=0)
    cost: int = 0
    optional: bool = False
    intensity: Intensity | None = None
    bookRequired: bool = False
    verification: Verification = "unverified"
    reason: str | None = None
    transitMinutes: int | None = None
    transitMode: LocalTransport | None = None
    address: str | None = None
    location: dict[str, float] | None = None
    poiId: str | None = None
    imageUrl: str | None = None
    mealType: str | None = None


class UpdateItineraryItemPayload(BaseModel):
    title: str | None = None
    startTime: str | None = None
    durationMin: int | None = Field(default=None, ge=0)
    stopType: StopType | None = None
    cost: int | None = Field(default=None, ge=0)
    reason: str | None = None


class DayWeather(BaseModel):
    icon: str
    desc: str
    range: str
    tip: str | None = None


class Stay(BaseModel):
    """当晚住宿片区。不推荐具体酒店——无法验证空房与价格。

    city 由所属 DayPlan.city 继承，不重复存储。
    """

    area: str
    location: dict[str, float] | None = None
    reason: str | None = None


class DayPlan(BaseModel):
    day: int
    date: str
    city: str
    title: str
    generationStatus: DayGenerationStatus = "finalized"
    weather: DayWeather
    stay: Stay | None = None
    items: list[ItineraryItem]


class Booking(BaseModel):
    """预订待办。名称与所需信息从 itemId 指向的条目取，不重复存储。"""

    itemId: str
    channel: str
    leadTimeDays: int | None = Field(default=None, ge=0)
    urgency: BookingUrgency | None = None
    note: str | None = None


class PlanNote(BaseModel):
    kind: NoteKind
    text: str


class Itinerary(BaseModel):
    tripId: str
    title: str
    dateRange: str
    originCity: str
    # route 是有序途经城市；destination 是它的展示摘要，保留是因为列表页与标题栏都在用
    destination: str
    route: list[str] = Field(default_factory=list)
    travelers: Travelers
    interests: list[str]
    notes: list[PlanNote] = Field(default_factory=list)
    bookings: list[Booking] = Field(default_factory=list)
    days: list[DayPlan]


class AgentJob(BaseModel):
    jobId: str
    tripId: str
    status: AgentJobStatus
    progress: int = Field(ge=0, le=100)
    message: str
