import type { Itinerary } from '../types/itinerary'

// 一个完整行程的详情数据 —— Mock 假数据。
// 页面不应直接 import 这个文件；请通过 api/trips.ts 的 getTripDetail 访问。

export const tokyoItinerary: Itinerary = {
  tripId: 't1',
  destination: '日本东京',
  title: '东京 7 日深度文化之旅',
  dateRange: '2024.03.15 – 03.21',
  travelers: 2,
  interests: ['文化历史', '美食探索', '自然风光'],
  days: [
    {
      day: 1,
      date: '3月15日',
      title: '浅草 · 秋叶原 · 上野',
      weather: { icon: '☀️', desc: '晴', range: '12–18°C', tip: '早晚温差大，建议带外套' },
      budget: { 交通: 400, 餐饮: 320, 门票: 80, 其他: 100 },
      route: { distanceKm: 10.2, walkKm: 2.8, transitKm: 7.4, durationLabel: '~8.5h' },
      items: [
        { id: 'i1', startTime: '09:00', endTime: '11:00', title: '浅草寺', type: '文化', durationLabel: '2h', cost: 0, reason: '东京最古老的寺院，感受江户风情', transitFromPrev: undefined },
        { id: 'i2', startTime: '11:00', endTime: '12:00', title: '仲见世购物街', type: '购物', durationLabel: '1h', cost: 0, transitFromPrev: '步行 5 分钟' },
        { id: 'i3', startTime: '13:30', endTime: '15:30', title: '秋叶原电器街', type: '购物', durationLabel: '2h', cost: 0, reason: '动漫与电器天堂', transitFromPrev: '地铁 20 分钟 · ¥180' },
        { id: 'i4', startTime: '16:00', endTime: '18:00', title: '上野公园 / 博物馆', type: '自然', durationLabel: '2h', cost: 80, transitFromPrev: '地铁 10 分钟 · ¥140' },
        { id: 'i5', startTime: '19:00', endTime: '21:00', title: '居酒屋晚餐 — 新宿', type: '美食', durationLabel: '2h', cost: 200, transitFromPrev: '步行 8 分钟' },
      ],
    },
    {
      day: 2,
      date: '3月16日',
      title: '新宿 · 涩谷 · 代官山',
      weather: { icon: '⛅', desc: '多云', range: '10–15°C', tip: '有风，注意保暖' },
      budget: { 交通: 350, 餐饮: 380, 门票: 500, 其他: 150 },
      route: { distanceKm: 8.6, walkKm: 3.1, transitKm: 5.5, durationLabel: '~8h' },
      items: [
        { id: 'i6', startTime: '09:00', endTime: '11:00', title: '新宿御苑', type: '自然', durationLabel: '2h', cost: 500, reason: '樱花季必访的都市庭园' },
        { id: 'i7', startTime: '11:30', endTime: '13:00', title: '新宿购物街', type: '购物', durationLabel: '1.5h', cost: 0, transitFromPrev: '步行 10 分钟' },
        { id: 'i8', startTime: '14:30', endTime: '15:30', title: '涩谷十字路口', type: '地标', durationLabel: '1h', cost: 0, transitFromPrev: '地铁 15 分钟 · ¥180' },
        { id: 'i9', startTime: '16:00', endTime: '18:00', title: '代官山 T-SITE', type: '文化', durationLabel: '2h', cost: 0, transitFromPrev: '步行 12 分钟' },
        { id: 'i10', startTime: '18:30', endTime: '20:00', title: '惠比寿花园广场', type: '休闲', durationLabel: '1.5h', cost: 0, transitFromPrev: '步行 10 分钟' },
      ],
    },
    {
      day: 3,
      date: '3月17日',
      title: '银座 · 筑地 · 台场',
      weather: { icon: '🌧️', desc: '小雨', range: '9–13°C', tip: '记得带伞，多安排室内' },
      budget: { 交通: 500, 餐饮: 500, 门票: 3200, 其他: 200 },
      route: { distanceKm: 12.8, walkKm: 2.2, transitKm: 10.6, durationLabel: '~9h' },
      items: [
        { id: 'i11', startTime: '08:00', endTime: '09:30', title: '筑地市场早餐', type: '美食', durationLabel: '1.5h', cost: 200, reason: '最新鲜的海鲜早餐' },
        { id: 'i12', startTime: '10:30', endTime: '12:30', title: '银座购物', type: '购物', durationLabel: '2h', cost: 0, transitFromPrev: '地铁 15 分钟 · ¥200' },
        { id: 'i13', startTime: '14:00', endTime: '15:30', title: '台场海滨公园', type: '自然', durationLabel: '1.5h', cost: 0, transitFromPrev: '百合鸥线 30 分钟 · ¥300' },
        { id: 'i14', startTime: '16:00', endTime: '19:00', title: 'teamLab 数字艺术', type: '艺术', durationLabel: '3h', cost: 3200, reason: '沉浸式数字艺术，雨天首选', transitFromPrev: '步行 5 分钟' },
      ],
    },
  ],
}
