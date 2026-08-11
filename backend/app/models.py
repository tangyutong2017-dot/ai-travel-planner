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


class ItineraryItem(BaseModel):
    id: str
    startTime: str
    endTime: str
    title: str
    type: str
    durationLabel: str
    cost: int
    reason: str | None = None
    transitFromPrev: str | None = None
    address: str | None = None
    location: dict[str, float] | None = None
    poiId: str | None = None
    source: str | None = None
    imageUrl: str | None = None
    mealType: str | None = None
    countsAsMajorPlace: bool = True


class UpdateItineraryItemPayload(BaseModel):
    title: str | None = None
    startTime: str | None = None
    endTime: str | None = None
    type: str | None = None
    durationLabel: str | None = None
    cost: int | None = Field(default=None, ge=0)
    reason: str | None = None


class DayRoute(BaseModel):
    distanceKm: float
    walkKm: float
    transitKm: float
    durationLabel: str


class DayWeather(BaseModel):
    icon: str
    desc: str
    range: str
    tip: str | None = None


class MealSuggestion(BaseModel):
    time: str
    area: str
    suggestion: str
    nearbyPlace: str | None = None
    reason: str | None = None


class DayMealSuggestions(BaseModel):
    breakfast: MealSuggestion
    lunch: MealSuggestion
    dinner: MealSuggestion


class DayPlan(BaseModel):
    day: int
    date: str
    title: str
    generationStatus: DayGenerationStatus = "finalized"
    weather: DayWeather
    mealSuggestions: DayMealSuggestions | None = None
    route: DayRoute
    items: list[ItineraryItem]


class Itinerary(BaseModel):
    tripId: str
    destination: str
    title: str
    dateRange: str
    travelers: int
    interests: list[str]
    days: list[DayPlan]


class AgentJob(BaseModel):
    jobId: str
    tripId: str
    status: AgentJobStatus
    progress: int = Field(ge=0, le=100)
    message: str
