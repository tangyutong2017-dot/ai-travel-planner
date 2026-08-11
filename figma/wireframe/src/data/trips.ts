// 「我的行程」页展示的行程列表 —— Mock 假数据
//
// 现在是写死的假数据，将来接后端后，这里会改成从接口获取。
// 好处：到时候只改这个文件，界面（App.tsx）一行都不用动。

export const trips = [
  { name: "东京 7 日文化之旅", date: "2024.03.15", dest: "日本东京", days: 7, status: "计划中" },
  { name: "巴黎浪漫蜜月", date: "2024.06.01", dest: "法国巴黎", days: 10, status: "草稿" },
  { name: "新加坡亲子游", date: "2023.12.20", dest: "新加坡", days: 5, status: "已完成" },
  { name: "北海道温泉之旅", date: "2023.02.10", dest: "日本北海道", days: 6, status: "已完成" },
  { name: "曼谷美食探索", date: "2023.09.05", dest: "泰国曼谷", days: 5, status: "已完成" },
  { name: "云南大理慢旅行", date: "2024.08.10", dest: "中国大理", days: 8, status: "草稿" },
];
