# 智能旅行规划助手 Figma 低保真设计说明 v0.1

## 1. 文档目的

本文档用于指导“智能旅行规划助手”的第一轮 Figma 低保真设计。

低保真阶段的目标不是做漂亮界面，而是验证产品流程、页面结构、信息层级和关键交互是否成立。此阶段应优先解决“页面怎么组织”“用户怎么走完整流程”“数据放在哪里”“编辑和输出如何区分”等问题。

## 2. 低保真设计目标

本阶段需要完成：

- 明确完整用户流程
- 画出 7 个核心页面
- 定义每个页面的信息结构
- 标出关键按钮和交互入口
- 区分“编辑工作台”和“输出方案页”
- 为后续高保真和前端 Mock 提供依据

本阶段暂不重点处理：

- 精细配色
- 品牌视觉
- 图片素材
- 复杂动效
- 最终组件样式
- 高德地图真实样式

## 3. 核心流程

低保真设计必须围绕以下主链路：

```text
创建行程页
→ 偏好设置页
→ 生成中页面
→ 行程结果工作台
→ 多轮 AI 调整 / 手动编辑
→ 点击输出方案
→ 输出方案页
→ 保存或导出 PDF
→ 我的行程页
```

关键原则：

- 行程结果页是“编辑工作台”
- 输出方案页是“最终展示页”
- 用户可以多轮编辑，直到主动点击“输出方案”
- PDF 导出内容来自输出方案页

## 4. Figma 文件建议结构

建议在 Figma 中建立以下 Pages：

1. Cover
2. User Flow
3. Wireframes
4. Components
5. Notes

### 4.1 Cover

内容：

- 项目名称：智能旅行规划助手
- 版本：Low-fidelity Wireframe v0.1
- 一句话定位：用 AI、地图路线和天气生成可编辑、可导出的旅行计划

### 4.2 User Flow

画主流程图即可，不需要复杂。

节点：

- 输入基础信息
- 设置偏好
- 生成计划
- 查看行程
- 编辑 / AI 调整
- 输出方案
- 导出 PDF

### 4.3 Wireframes

放 7 个核心页面的低保真线框。

### 4.4 Components

先画基础组件：

- Button
- Input
- Select
- Tag
- Date Tabs
- Timeline Item
- 景点卡片
- 天气卡片
- 路线摘要卡片
- 地图预览区域
- AI 调整输入框
- 输出方案计划表

### 4.5 Notes

记录暂时不确定的问题，例如：

- 行程结果页采用两栏还是三栏？
- AI 输入框放底部还是右侧？
- 输出方案页是长页面还是分页预览？

## 5. 页面低保真说明

### 5.1 创建行程页

页面目标：

- 让用户快速开始创建旅行计划
- 收集最基础、最影响生成结果的信息

页面结构建议：

```text
顶部导航
主标题
基础信息表单
兴趣快速标签
主要按钮：下一步
```

必须包含：

- 目的地输入
- 出行人数
- 旅行天数或日期
- 预算
- 旅行节奏
- 兴趣标签
- 下一步按钮

低保真重点：

- 表单不要太散
- 兴趣标签要比长文本更醒目
- 下一步按钮位置明确

暂不需要：

- 大幅营销 hero
- 大量装饰图片
- 复杂登录入口

## 5.2 偏好设置页

页面目标：

- 收集更细的偏好，让 AI 生成更精准

页面结构建议：

```text
步骤提示
偏好分组
自定义偏好输入框
返回 / 生成旅行计划按钮
```

必须包含：

- 同行人类型
- 必去景点
- 不想去景点
- 饮食偏好
- 出行方式偏好
- 自定义偏好
- 生成旅行计划按钮

低保真重点：

- 页面要表现“这是补充偏好”，不要像重新填一遍表单
- 必去 / 不想去景点适合用标签输入样式
- 自定义偏好给用户自由表达空间

## 5.3 生成中页面

页面目标：

- 缓解等待焦虑
- 让用户知道系统正在结合 AI、地图路线和天气生成计划

页面结构建议：

```text
生成状态标题
步骤列表
进度反馈
轻量提示文案
```

生成步骤：

- 分析旅行偏好
- 推荐合适景点
- 补全地图位置
- 计算路线耗时
- 匹配天气信息
- 生成每日计划

低保真重点：

- 不需要复杂动画
- 要让用户相信系统在做有价值的规划

## 5.4 行程结果页

页面目标：

- 展示生成结果
- 支持用户反复编辑和 AI 调整
- 是整个产品最核心页面

推荐布局：

```text
顶部：目的地 / 日期 / 人数 / 输出方案按钮
左侧：日期 Tabs + 每日时间线
中间：景点卡片 / 行程详情
右侧：地图预览 / 路线摘要 / 天气 / 预算
底部或右侧：AI 调整输入框
```

必须包含：

- 目的地和行程概览
- Day Tabs
- 每日主题
- 时间线
- 景点卡片
- 景点操作按钮
- 地图预览
- 路线摘要
- 天气卡片
- 预算概览
- AI 调整输入框
- 输出方案按钮

景点卡片内容：

- 时间
- 景点名称
- 类型
- 推荐理由
- 停留时长
- 预计花费
- 到下一个景点的交通耗时
- 编辑 / 替换 / 删除入口

低保真重点：

- 这页不要做成聊天页
- AI 输入框是辅助，不是唯一交互
- 输出方案按钮要明显，但不能打断编辑
- 地图、路线、天气是计划判断信息，不只是装饰

建议先画桌面端：

- 因为行程工作台信息量较大
- 桌面端更适合展示作品集和后续开发

## 5.5 景点详情弹窗

页面目标：

- 查看和编辑单个景点详情

弹窗结构：

```text
景点名称
类型 / 地址
推荐理由
停留时长
预计花费
交通提示
用户备注
底部操作按钮
```

必须包含：

- 保存修改
- 替换景点
- 删除景点
- 关闭

低保真重点：

- 弹窗不要承载太多复杂功能
- 主要用于局部查看和编辑

## 5.6 输出方案页

页面目标：

- 展示最终美观旅行计划
- 为 PDF 导出提供稳定版式

页面结构建议：

```text
顶部：返回编辑 / 保存 / 导出 PDF
封面信息：目的地、日期、人数、预算
Day 1 计划表
Day 2 计划表
Day 3 计划表
预算汇总
备注
```

每日计划表必须包含：

- 日期
- 天气
- 当日主题
- 时间线
- 地图概览
- 路线摘要
- 景点与交通信息
- 预算和备注

低保真重点：

- 这页要和行程结果页区分开
- 行程结果页像工作台
- 输出方案页像最终成品
- 视觉空间可以更大、更清晰

## 5.7 我的行程页

页面目标：

- 管理已保存的旅行计划

页面结构建议：

```text
顶部标题
行程列表
行程卡片
```

行程卡片内容：

- 目的地
- 日期或天数
- 人数
- 预算
- 最近编辑时间
- 状态：草稿 / 已输出 / 已导出
- 继续编辑按钮

低保真重点：

- MVP 简单即可
- 不需要复杂搜索筛选

## 6. 关键组件说明

### 6.1 Timeline Item

用于展示某一天里的一个行程安排。

字段：

- 开始时间
- 结束时间
- 景点名称
- 类型
- 停留时长
- 交通耗时
- 操作入口

### 6.2 景点卡片

用于展示景点的推荐和编辑信息。

字段：

- 名称
- 推荐理由
- 地址
- 预计花费
- 停留时长
- 编辑 / 替换 / 删除

### 6.3 路线摘要卡片

用于帮助用户判断行程是否顺路。

字段：

- 当日总距离
- 总交通时间
- 分段路线
- 交通方式

### 6.4 天气卡片

用于辅助用户理解当天出行条件。

字段：

- 天气状态
- 温度区间
- 降雨提示
- 出行建议

### 6.5 AI 调整输入框

用于多轮调整行程。

示例提示：

- 第二天轻松一点
- 多加一些本地美食
- 下雨天尽量安排室内景点
- 预算控制在 3000 元以内

## 7. Figma Make 提示词

### 7.1 低保真总提示词

```text
Create a low-fidelity wireframe for an AI travel planning web app.

The app helps users input destination, travelers, travel days, interests, pace, and custom preferences. It generates an editable itinerary with daily timeline, attraction cards, map preview, route summary, weather card, budget summary, AI adjustment input, and an output plan button.

Pages:
1. Create trip page
2. Preference setup page
3. Generating page
4. Editable itinerary workspace
5. Attraction detail modal
6. Output plan preview page
7. My trips page

Style: low fidelity wireframe, grayscale, clear layout, desktop web app, product tool interface, no marketing landing page.
```

### 7.2 行程结果页提示词

```text
Create a low-fidelity desktop wireframe for the main itinerary workspace of an AI travel planning app.

The page should include:
- top trip summary with destination, dates, travelers, budget, and output plan button
- day tabs
- daily timeline with attraction cards
- map preview with numbered attraction points
- route summary card
- weather card
- budget summary
- AI adjustment input box
- edit, replace, delete actions on itinerary items

The page is a planning workspace, not a chat page. Use grayscale wireframe style.
```

### 7.3 输出方案页提示词

```text
Create a low-fidelity wireframe for the output plan preview page of an AI travel itinerary app.

The page shows the final travel plan after the user clicks "Output Plan". It should look like a clean printable itinerary preview.

Include:
- trip cover summary
- one card or section per day
- weather for each day
- timeline schedule
- map preview
- route summary
- attraction and transportation details
- budget summary
- buttons for back to edit, save, and export PDF

Style: grayscale wireframe, clean printable layout, not a marketing landing page.
```

## 8. 低保真验收标准

完成低保真后，需要检查：

- 是否能看懂完整用户流程
- 是否明确区分编辑页和输出页
- 是否能看到 AI 调整入口
- 是否能看到输出方案按钮
- 是否能看到地图、路线、天气、预算的位置
- 是否能看出 PDF 导出来自输出方案页
- 是否避免做成单纯聊天页面
- 是否避免做成营销落地页

## 9. 下一步

完成 Figma 低保真后，下一步进行：

1. 低保真评审
2. 确认行程结果页布局
3. 确认输出方案页版式
4. 建立基础组件库
5. 进入高保真视觉设计
