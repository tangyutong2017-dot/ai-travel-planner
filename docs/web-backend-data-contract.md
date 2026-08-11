# Web 后端数据需求

## 前端路由

当前前端使用浏览器 History API 路由，后续可以平滑替换为 `react-router`。

- `/trips`：我的行程列表
- `/trips/new`：创建行程向导
- `/trips/:tripId/workspace`：行程工作区，进入后请求 `GET /api/trips/:tripId`
- `/trips/:tripId/output`：输出预览

## 我的行程列表

接口：`GET /api/trips`

查询参数：

- `status`: 可选，`planned` 或 `completed`；不传返回全部
- `sort`: 可选，默认 `updatedAt_desc`
- `keyword`: 可选，搜索行程名称或目的地

返回字段：

```ts
type TripListResponse = {
  items: Trip[]
  summary: {
    total: number
    planned: number
    completed: number
    totalDays: number
    destinationCount: number
    attractionCount: number
  }
}

type Trip = {
  id: string
  name: string
  dest: string
  days: number
  date: string
  status: 'planned' | 'completed'
  coverUrl?: string
  updatedAt?: string
  attractionCount?: number
}
```

`summary` 统计的是**当前筛选结果**，不是全库，因此 `summary.total` 恒等于
`items.length`。切换筛选或搜索时统计条会跟着变。

前端展示逻辑：

- 点击 `全部`：请求 `GET /api/trips`
- 点击 `计划中`：请求 `GET /api/trips?status=planned`
- 点击 `已完成`：请求 `GET /api/trips?status=completed`
- 状态标签颜色：`planned` 蓝色，`completed` 绿色
- `items` 为空时显示空结果提示
- 卡片点击后需要用 `id` 打开详情：`GET /api/trips/:id`

## 行程详情 / 工作区

接口：`GET /api/trips/:tripId`

用途：进入行程工作区时获取完整行程详情。前端会用这些数据渲染左侧天数、中心时间轴、右侧地图/天气/备注。

返回：

```ts
type Itinerary = {
  tripId: string
  destination: string
  title: string
  dateRange: string
  travelers: number
  interests: string[]
  days: DayPlan[]
}

type DayPlan = {
  day: number
  date: string
  title: string
  weather: {
    icon: string
    desc: string
    range: string
    tip?: string
  }
  route: {
    distanceKm: number
    walkKm: number
    transitKm: number
    durationLabel: string
  }
  items: ItineraryItem[]
}

type ItineraryItem = {
  id: string
  startTime: string
  endTime: string
  title: string
  type: string
  durationLabel: string
  cost: number
  reason?: string
  transitFromPrev?: string
}
```

## 创建行程向导

接口一：`POST /api/trips`

用途：保存用户在创建向导里填写的基础信息和偏好设置，创建一条新的计划中行程。

请求体：

```ts
type CreateTripPayload = {
  destination: string
  startDate: string
  endDate: string
  days: number
  originCity: string
  intercityTransport: 'flight' | 'train' | 'selfDrive' | 'mixed'
  travelers: {
    adults: number
    children: number
    infants: number
  }
  travelParty: 'solo' | 'couple' | 'friends' | 'family' | 'multigenerational'
  visitHistory: 'first' | 'returning'
  preferences: {
    interests: string[]
    pace: 'packed' | 'balanced' | 'relaxed'
    localTransport: ('walking' | 'transit' | 'driving')[]
    comfortLevel: 'budget' | 'standard' | 'comfort' | 'luxury'
    activityLevel: 'low' | 'medium' | 'high'
    customText: string
  }
}
```

返回：

```ts
type CreateTripResponse = {
  tripId: string
}
```

接口二：`POST /api/trips/:tripId/generate`

用途：启动后端 agent 生成行程。

返回：

```ts
type GenerateTripResponse = {
  tripId: string
  jobId: string
}
```

后续建议：

- 前端拿到 `jobId` 后轮询 `GET /api/jobs/:jobId`
- job 成功后跳转 `GET /api/trips/:tripId` 对应的工作区
- job 失败时返回可展示的 `message`，前端显示重试

接口三：`GET /api/jobs/:jobId`

用途：查询后端 agent 的生成任务进度。

返回：

```ts
type AgentJob = {
  jobId: string
  tripId: string
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  progress: number
  message: string
}
```


## 已移除：预算

`CreateTripPayload.budget` 与 `DayPlan.budget` 已于 2026-08-11 移除。

原因：高德 POI 的 `cost` 字段覆盖率低，餐饮与交通费用没有可靠数据源，
加总出的"总预算"实为估算，可信度不足以支撑一个独立的输出页。

保留的是**单个景点的真实门票价**（`ItineraryItem.cost`，来自高德），
在景点卡片上如实展示"免费 / ¥80"，但不做任何加总与超支校验。


## 输入层改版（2026-08-11）

### 新增

| 字段 | 为什么需要 |
|---|---|
| `originCity` | 没有出发地就无法推算首日几点能开始玩、末日几点必须收工 |
| `intercityTransport` | 飞机与高铁的到达时间差异显著，直接影响首末日可用时长 |
| `travelParty` | 人数给精确值，关系给语义——同样 2 个成人，情侣与朋友的行程不同 |
| `visitHistory` | 二刷需要避开首刷已打卡的热门点 |
| `preferences.comfortLevel` | 定性档次，不需要价格数据源即可影响餐饮与住宿片区取向 |
| `preferences.activityLevel` | 带老人或体力受限时，长距离徒步是**硬约束**而非偏好，属安全范畴 |

### 修改

- `preferences.pace`：`1..100` 数值 → `'packed' | 'balanced' | 'relaxed'` 枚举。
  原数值精度是假的（代码本就压成三档），且节奏语义交由 LLM 理解，标签比数字信息量大。
- `preferences.transport` → `preferences.localTransport`，并由 5 个选项收敛为 3 个。
  改名是为了与新增的城际交通区分；收敛是因为自驾 / 打车 / 包车在路线计算上完全等价，
  让用户在不产生任何差异的选项间做选择是种伪装。若将来要建模停车，可再拆开。

### 删除

- `preferences.accommodation`（酒店/民宿/青旅/度假村/精品酒店）：全后端零引用。
  产品只输出「建议住宿片区」而不推荐具体酒店，住宿类型不改变任何输出，
  其意图已由 `comfortLevel` 覆盖。
