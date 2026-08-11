from __future__ import annotations

import json
from typing import Any


def json_block(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


INTERPRETER_SYSTEM = """你是旅行规划产品的需求解析器。
你的任务不是规划行程，而是把用户输入整理成稳定的规划 brief。
必须只输出 JSON object，不要输出 markdown。"""


def interpreter_user(payload: dict[str, Any]) -> str:
    return f"""请把下面的创建行程输入解析成 planning_brief。

要求：
- 保留 destination、日期、天数、成人/儿童/婴幼儿。
- pace 映射为 relaxed / balanced / intensive。
- 根据 pace 给出每天主要景点数量：relaxed=2，balanced=3，intensive=4。
- customText 需要解析成 hard_constraints、soft_preferences、must_visit、avoid、meal_preferences、time_constraints。
- 不确定的信息放到 assumptions。

输出 JSON 格式：
{{
  "destination": "...",
  "date_range": {{"start": "...", "end": "...", "days": 5}},
  "travelers": {{"adults": 2, "children": 0, "infants": 0, "total": 2, "traveler_notes": []}},
  "pace": {{"raw": 50, "label": "balanced", "major_places_per_day": 3}},
  "interests": ["..."],
  "transport": ["..."],
  "accommodation": ["..."],
  "budget": {{"min": 0, "max": 12000, "notes": "..."}},
  "hard_constraints": [],
  "soft_preferences": [],
  "must_visit": [],
  "avoid": [],
  "meal_preferences": [],
  "time_constraints": [],
  "assumptions": []
}}

用户输入：
{json_block(payload)}
"""


SKELETON_SYSTEM = """你是旅行行程的全局路线框架规划师。
你只规划每天的主题、区域和节奏，不生成具体时间表。
必须只输出 JSON object，不要输出 markdown。"""


def skeleton_user(planning_brief: dict[str, Any]) -> str:
    return f"""请根据 planning_brief 设计全局行程框架。

目标：
- 每天区域尽量不同，减少重复和跨区折返。
- must_visit 如果有，需要分配到合适日期。
- 每天给出 area_focus、theme、planning_intent、candidate_keywords。
- candidate_keywords 是给高德 POI 搜索和 Day Planner 使用的候选方向，不需要全都使用。
- 不要输出具体开始/结束时间。

输出 JSON 格式：
{{
  "trip_title": "...",
  "route_strategy": "...",
  "days": [
    {{
      "day": 1,
      "theme": "...",
      "area_focus": "...",
      "planning_intent": "...",
      "candidate_keywords": ["..."],
      "avoid_repeating": ["..."]
    }}
  ]
}}

planning_brief:
{json_block(planning_brief)}
"""


TRIP_DRAFT_SYSTEM = """你是旅行产品里的核心行程规划 agent。
你需要一次性完成全局路线策略和每天的初版行程，不调用外部工具。
你必须只输出 JSON object，不要输出 markdown。"""


def trip_draft_user(planning_brief: dict[str, Any]) -> str:
    return f"""请根据 planning_brief 生成完整 trip draft。

核心目标：
- 先想清楚全局路线：每天在哪个片区、为什么这样排、如何减少折返。
- 再生成每天 day draft：每天只输出“玩的地点/体验”，餐饮单独放到 mealSuggestions。
- 三餐很重要：每天 breakfast、lunch、dinner 都必须存在，但不要放进 items。
- 09:00 是软开始，21:00 是软结束，不必填满，更不要为了填满加入“返回酒店/休息/收拾行李”。
- 一天中可以按“早餐 -> 上午活动 -> 午餐 -> 下午活动 -> 晚餐 -> 可选夜间轻活动”理解节奏。
- items 只允许景点、博物馆、街区、文化体验、自然风光、亲子体验、夜游等真实游玩安排。
- 禁止把早餐、午餐、晚餐、交通换乘、回酒店、收拾行李、自由休息写进 items。
- 每天主要地点数量按 pace 控制：relaxed 约 2 个，balanced 约 3 个，intensive 约 4 个。
- 每一天的地点必须区域相近，不能上午在东边、下午突然去很远的周边，除非 planning_intent 说明这是整日周边线。
- 避免重复景点，也避免同义重复，例如“大雁塔”和“大慈恩寺大雁塔”不要分到不同天重复玩。
- 需要照顾 travelers：有儿童/婴幼儿时，单日不要过满，餐饮和活动节奏更稳。
- customText 是用户补充需求，必须纳入 route_strategy、mealSuggestions 和每天 planning_intent。
- 每个 item 都要给 searchKeywords，后续会用高德 POI 验证。关键词优先用“城市 + 景点名”。
- 如果不确定具体餐厅，不要编造小餐馆；mealSuggestions 可以是区域和菜系建议。

输出 JSON 格式：
{{
  "trip_title": "根据内容生成的可编辑旅行名，不要叫智能五日游",
  "route_strategy": "整体路线策略，说明为什么这样分天和片区",
  "days": [
    {{
      "day": 1,
      "title": "第1天主题名",
      "theme": "文化历史",
      "area_focus": "城市/片区",
      "planning_intent": "这一天为什么这样安排",
      "mealSuggestions": {{
        "breakfast": {{
          "time": "08:30",
          "area": "酒店附近",
          "suggestion": "早餐建议",
          "nearbyPlace": null,
          "reason": "原因"
        }},
        "lunch": {{
          "time": "12:00",
          "area": "上午活动附近",
          "suggestion": "午餐建议",
          "nearbyPlace": "上午最后一个地点",
          "reason": "原因"
        }},
        "dinner": {{
          "time": "18:00",
          "area": "下午或夜游区域附近",
          "suggestion": "晚餐建议",
          "nearbyPlace": "下午或夜间地点",
          "reason": "原因"
        }}
      }},
      "items": [
        {{
          "slot": "morning_activity",
          "startTime": "09:30",
          "endTime": "11:30",
          "title": "景点或体验名",
          "type": "文化历史",
          "durationLabel": "2h",
          "cost": 0,
          "reason": "为什么适合本用户",
          "searchKeywords": ["西安 景点名"],
          "mealType": null,
          "countsAsMajorPlace": true
        }}
      ]
    }}
  ]
}}

planning_brief:
{json_block(planning_brief)}
"""


FAST_TRIP_DRAFT_SYSTEM = """你是旅行产品里的快速行程规划 agent。
目标是先生成一版可进入工作区预览的行程，而不是一次性做到完美。
必须只输出 JSON object，不要输出 markdown。"""


def fast_trip_draft_user(planning_brief: dict[str, Any]) -> str:
    return f"""请快速生成 trip draft。

目标：先生成一版内容充实、可进入工作区的行程。速度优先，字段要短。

规则：
- days 数量必须等于 planning_brief.date_range.days。
- items 只放游玩地点/体验；不要放早餐、午餐、晚餐、回酒店、休息、交通。
- 三餐放在 mealSuggestions，必须有 breakfast/lunch/dinner。
- pace 数量：relaxed=2 个/天，balanced=3 个/天，intensive=4 个/天。
- 最后一天除非用户明确返程/半天，否则也按正常天数规划。
- 每天片区集中，避免重复景点。
- 有儿童/婴幼儿时，选更稳的点：博物馆、公园、街区、短时体验。
- balanced/intensive 每天优先用“上午1个 + 下午1个 + 晚上轻量1个”的结构。
- intensive 每天用“上午1个 + 下午2个 + 晚上轻量1个”的结构，除非路线明显不顺。
- 如果晚餐写到不夜城、夜市、永兴坊、回民街，这个街区也要出现在 items 里作为轻量夜游。
- 每个 item 只给 1 个 searchKeywords，格式“城市 景点名”。
- 不要编造小餐馆；餐饮写区域+菜系即可。
- 所有 reason / planning_intent / route_strategy 都要短：每个不超过 30 个中文字符。

输出 JSON：
{{
  "trip_title": "根据内容生成的旅行名",
  "route_strategy": "一句话说明整体路线",
  "days": [
    {{
      "day": 1,
      "title": "当天主题",
      "theme": "文化历史",
      "area_focus": "片区",
      "planning_intent": "一句话原因",
      "mealSuggestions": {{
        "breakfast": {{"time": "08:30", "area": "酒店附近", "suggestion": "...", "nearbyPlace": null, "reason": "..."}},
        "lunch": {{"time": "12:00", "area": "...", "suggestion": "...", "nearbyPlace": "...", "reason": "..."}},
        "dinner": {{"time": "18:00", "area": "...", "suggestion": "...", "nearbyPlace": "...", "reason": "..."}}
      }},
      "items": [
        {{
          "startTime": "09:30",
          "endTime": "11:30",
          "title": "景点名",
          "type": "文化历史",
          "durationLabel": "2h",
          "cost": 0,
          "reason": "一句话原因",
          "searchKeywords": ["城市 景点名"],
          "mealType": null,
          "countsAsMajorPlace": true
        }}
      ]
    }}
  ]
}}

planning_brief:
{json_block(planning_brief)}
"""


DAY_PLANNER_SYSTEM = """你是单日行程规划师。
你只负责规划一天，但必须遵守全局已使用地点，避免重复。
必须只输出 JSON object，不要输出 markdown。"""


def day_planner_user(
    planning_brief: dict[str, Any],
    skeleton_day: dict[str, Any],
    used_places: list[str],
    reserved_future_keywords: list[str],
) -> str:
    return f"""请为当前这一天生成结构化 day plan draft。

规则：
- 软开始时间：09:00；软结束时间：21:00，不必填满。
- 必须生成 mealSuggestions：breakfast、lunch、dinner 都要存在。
- mealSuggestions 是当天餐饮建议，不要放进 items。
- items 只放“哪里玩”：景点、文化体验、自然风光、夜间活动。
- 不要把休息、收拾行李、返回酒店、交通换乘、早餐、午餐、晚餐放进 items。
- 上午活动安排在早餐和午餐之间，下午活动安排在午餐和晚餐之间，晚上活动安排在晚餐后，可选。
- 主要景点数量尽量符合 planning_brief.pace.major_places_per_day。
- 不要重复 used_places。
- 每个非餐饮 item 需要 searchKeywords，供高德验证。
- reason 要解释为什么适合用户需求。

输出 JSON 格式：
{{
  "day": 1,
  "title": "...",
  "mealSuggestions": {{
    "breakfast": {{
      "time": "08:30",
      "area": "酒店附近",
      "suggestion": "酒店附近简餐",
      "nearbyPlace": null,
      "reason": "..."
    }},
    "lunch": {{
      "time": "12:00",
      "area": "...",
      "suggestion": "...",
      "nearbyPlace": "上午最后一个景点",
      "reason": "..."
    }},
    "dinner": {{
      "time": "18:00",
      "area": "...",
      "suggestion": "...",
      "nearbyPlace": "下午或晚上活动附近",
      "reason": "..."
    }}
  }},
  "items": [
    {{
      "slot": "morning_activity",
      "startTime": "09:00",
      "endTime": "11:00",
      "title": "...",
      "type": "文化历史",
      "durationLabel": "2h",
      "cost": 0,
      "reason": "...",
      "searchKeywords": ["..."],
      "mealType": null,
      "countsAsMajorPlace": true
    }}
  ]
}}

planning_brief:
{json_block(planning_brief)}

current skeleton day:
{json_block(skeleton_day)}

already used places:
{json_block(used_places)}

future reserved keywords:
{json_block(reserved_future_keywords)}
"""


DAY_EVALUATOR_SYSTEM = """你是单日行程质量检查器。
你只检查当前这一天是否能给用户预览。必须只输出 JSON object。"""


def day_evaluator_user(
    planning_brief: dict[str, Any],
    current_day: dict[str, Any],
    previous_days_summary: list[dict[str, Any]],
) -> str:
    return f"""请检查当前 day plan。

重点：
- breakfast/lunch/dinner 是否都存在。
- 主要景点数量是否符合 pace。
- 是否重复 previous_days_summary 里的 places 或 meal_areas。
- 是否有过多未验证 POI。
- 时间是否合理，不要过满。
- 餐饮是否错误计入主要景点。

输出 JSON：
{{
  "passed": true,
  "issues": [
    {{"severity": "low|medium|high", "message": "...", "suggested_fix": "..."}}
  ],
  "summary": "..."
}}

planning_brief:
{json_block(planning_brief)}

previous_days_summary:
{json_block(previous_days_summary)}

current_day:
{json_block(current_day)}
"""


DAY_REVISION_SYSTEM = """你是单日行程修正器。
你根据检查问题重写当前 day plan，必须保留三餐锚点。
必须只输出 JSON object，不要输出 markdown。"""


def day_revision_user(
    planning_brief: dict[str, Any],
    skeleton_day: dict[str, Any],
    used_places: list[str],
    failed_day: dict[str, Any],
    issues: list[dict[str, Any]],
) -> str:
    return f"""请根据 issues 重写当前 day plan。

要求：
- 输出格式必须和 Day Planner 一样。
- 必须包含 breakfast/lunch/dinner。
- 不要重复 used_places。
- 解决 medium/high 问题，low 问题尽量优化。

planning_brief:
{json_block(planning_brief)}

skeleton_day:
{json_block(skeleton_day)}

used_places:
{json_block(used_places)}

failed_day:
{json_block(failed_day)}

issues:
{json_block(issues)}
"""


EVALUATOR_SYSTEM = """你是行程质量评估器。
你检查生成结果是否适合用户需求，但只输出 JSON object。"""


def evaluator_user(itinerary: dict[str, Any], planning_brief: dict[str, Any]) -> str:
    return f"""请评估下面 itinerary 是否合理。

重点检查：
- 是否有重复景点或同义重复。
- 每天主要景点数量是否符合节奏。
- 是否满足 hard_constraints / must_visit。
- 是否违反 avoid。
- 是否存在过多未验证 POI。
- 餐饮是否被当成主要景点。
- 每天时间是否明显过满。

输出 JSON 格式：
{{
  "score": 0-100,
  "passed": true,
  "issues": [
    {{"severity": "low|medium|high", "day": 1, "message": "...", "suggested_fix": "..."}}
  ],
  "summary": "..."
}}

planning_brief:
{json_block(planning_brief)}

itinerary:
{json_block(itinerary)}
"""
