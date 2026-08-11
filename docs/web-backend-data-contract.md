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

前端展示逻辑：

- 点击 `全部`：请求 `GET /api/trips`
- 点击 `计划中`：请求 `GET /api/trips?status=planned`
- 点击 `已完成`：请求 `GET /api/trips?status=completed`
- 状态标签颜色：`planned` 蓝色，`completed` 绿色
- `items` 为空时显示空结果提示
- 卡片点击后需要用 `id` 打开详情：`GET /api/trips/:id`

## 行程详情 / 工作区

接口：`GET /api/trips/:tripId`

用途：进入行程工作区时获取完整行程详情。前端会用这些数据渲染左侧天数、中心时间轴、右侧地图/天气/预算/备注。

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
  budget: {
    交通: number
    餐饮: number
    门票: number
    其他: number
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
  travelers: {
    adults: number
    children: number
    infants: number
  }
  budget: {
    min: number
    max: number
    level: '经济型' | '舒适型' | '豪华型'
  }
  preferences: {
    interests: string[]
    pace: number
    transport: string[]
    accommodation: string[]
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
