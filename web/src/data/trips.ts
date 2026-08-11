import type { Trip } from '../types/trip'

// 「我的行程」列表数据 —— Mock 假数据。
// 页面不应直接 import 这个文件；请通过 api/trips.ts 访问，方便后续替换为真实后端。

export const trips: Trip[] = [
  { id: 't1', name: '东京 7 日文化之旅', dest: '日本东京', days: 7, date: '2024.03.15', status: '计划中' },
  { id: 't2', name: '巴黎浪漫蜜月', dest: '法国巴黎', days: 10, date: '2024.06.01', status: '计划中' },
  { id: 't3', name: '新加坡亲子游', dest: '新加坡', days: 5, date: '2023.12.20', status: '已完成' },
  { id: 't4', name: '北海道温泉之旅', dest: '日本北海道', days: 6, date: '2023.02.10', status: '已完成' },
  { id: 't5', name: '曼谷美食探索', dest: '泰国曼谷', days: 5, date: '2023.09.05', status: '已完成' },
  { id: 't6', name: '云南大理慢旅行', dest: '中国大理', days: 8, date: '2024.08.10', status: '计划中' },
]
