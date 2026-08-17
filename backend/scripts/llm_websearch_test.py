"""带联网搜索的规划测试。

与 llm_reliability_test.py 对照，两处不同：
1. 给模型 web_search 工具，让它边推理边查
2. schema 去掉 start 与 transit_from_prev_min —— 实测这两个字段是耗时大头（98s → 22s），
   且模型给的通勤时间系统性低估，本就该由地图 API 算

产出后仍用高德核对：地点是否真实存在、同日是否地理集中。
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from math import cos, radians, sqrt

sys.path.insert(0, "/Users/yutongtang/Desktop/Exercise/travel-planner/backend")

from app.amap import search_poi  # noqa: E402
from app.llm import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL  # noqa: E402
from app.websearch import WEB_SEARCH_TOOL, as_tool_result, is_websearch_configured, web_search  # noqa: E402

MODEL = sys.argv[1] if len(sys.argv) > 1 else "deepseek-v4-flash"
SCENARIO = sys.argv[2] if len(sys.argv) > 2 else "dali"
MAX_ROUNDS = 3

# 多个场景用于压力测试：大理是基准（短程、平原、单城市），
# 西藏用来检验长行程、高原安全、多城市与超长点间距离。
SCENARIOS = {
    "dali": {
        "city": "大理",
        "brief": """为一家三口规划云南大理 3 日行程（2026-09-01 至 09-03）。
成人 2 人、儿童 1 人（8 岁），从北京飞往大理。
慢节奏、低体力（父母膝盖不好，爬不了长台阶）、不吃辣、想看洱海日落。""",
        # 同日最远两点的告警阈值（km）。城市短程行程，超过 30km 基本意味着跨片区折返
        "spread_warn": 15,
        "spread_bad": 30,
    },
    "tibet": {
        "city": "拉萨",
        "brief": """为两位朋友规划西藏 5 日行程（2026-09-10 至 09-14）。
成人 2 人（28 岁、31 岁），从成都飞往拉萨。
适中节奏、体力中等、首次进藏有高反顾虑、想看纳木错和布达拉宫。""",
        # 西藏点间距离本就极大——纳木错距拉萨约 250km，当日往返是常规安排，
        # 用城市尺度的阈值会把合理行程误判为折返
        "spread_warn": 120,
        "spread_bad": 300,
    },
}

CITY = SCENARIOS[SCENARIO]["city"]

SYSTEM = """你是旅行行程规划师。

可以用 web_search 查地图数据给不了的信息：景区无障碍设施（电瓶车/索道/台阶）、
是否需预约、门票与老人儿童优惠、日出日落时间、季节性景观时段。
请把相关问题合并成一次调用，不要逐条搜。

【最重要的格式要求】每条行程要分开写两个字段：

  name  —— 纯地点名，必须能在地图 App 里原样搜到。
           只写地名本身，不要加括号、不要加说明、不要写"午餐""入住"这类动作。
           没有对应地点的条目（航班、接驳、自由活动）留空字符串。
  label —— 给用户看的展示文案，可以自由发挥。

  正确：  name="崇圣寺三塔文化旅游区"   label="崇圣寺三塔（园内电瓶车代步）"
          name="喜洲古镇"              label="喜洲午餐 · 破酥粑粑"
          name=""                     label="北京 → 大理 直飞航班"
  错误：  name="午餐（免辣）"           ← 不是地名
          name="大理古城酒店（入住）"     ← 混入了动作与括号
          name="大理古城漫游（人民路）"   ← 混入了说明

其余要求：
- 同一天的地点应集中在同一片区，不要跨区往返
- 首日与末日必须包含城际交通
- 不要输出具体时刻，也不要估算通勤时间——这两项由系统用地图 API 计算"""

BRIEF = SCENARIOS[SCENARIO]["brief"] + """

最终只输出 JSON：
{"title":"...","days":[{"day":1,"theme":"...","stops":[
 {"name":"纯地点名或空字符串","label":"展示文案",
  "type":"sight|food|activity|hotel|flight|transfer",
  "duration_min":120,"reason":"...","note":"预约/电瓶车/优惠等实用提示"}]}]}"""


def post(body):
    request = urllib.request.Request(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        data=json.dumps(body).encode(),
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


def km(a, b):
    lat_mid = radians((a["lat"] + b["lat"]) / 2)
    return sqrt(((b["lng"] - a["lng"]) * cos(lat_mid)) ** 2 + (b["lat"] - a["lat"]) ** 2) * 111.0


def run():
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": BRIEF}]
    totals = {"prompt": 0, "completion": 0, "reasoning": 0}
    searched, llm_seconds, search_seconds = [], 0.0, 0.0

    for rnd in range(MAX_ROUNDS + 1):
        body = {"model": MODEL, "messages": messages, "temperature": 0.4}
        # 还允许搜索时挂工具；最后一轮强制收敛为 JSON
        if rnd < MAX_ROUNDS:
            body["tools"] = [WEB_SEARCH_TOOL]
        else:
            body["response_format"] = {"type": "json_object"}

        t0 = time.time()
        data = post(body)
        llm_seconds += time.time() - t0

        usage = data.get("usage", {})
        totals["prompt"] += usage.get("prompt_tokens", 0)
        totals["completion"] += usage.get("completion_tokens", 0)
        totals["reasoning"] += (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)

        message = data["choices"][0]["message"]
        calls = message.get("tool_calls")
        if not calls:
            return message.get("content", ""), totals, searched, llm_seconds, search_seconds

        messages.append(message)
        for call in calls:
            args = json.loads(call["function"]["arguments"] or "{}")
            queries = args.get("queries") or []
            searched.extend(queries)
            print(f"  第 {rnd + 1} 轮搜索：{queries}")

            t0 = time.time()
            results = web_search(queries)
            search_seconds += time.time() - t0

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": as_tool_result(results),
            })

    return "", totals, searched, llm_seconds, search_seconds


def main():
    if not is_websearch_configured():
        print("TAVILY_API_KEY 未配置——请先写入 backend/.env")
        return

    print(f"=== {MODEL} · {SCENARIO}（{CITY}）· 带联网搜索 ===")
    started = time.time()
    content, totals, searched, llm_seconds, search_seconds = run()
    wall = time.time() - started

    print(f"\n总耗时 {wall:.1f}s（LLM {llm_seconds:.1f}s + 搜索 {search_seconds:.1f}s）")
    print(f"搜索 {len(searched)} 条 | 输入 {totals['prompt']} 输出 {totals['completion']}"
          f"（推理 {totals['reasoning']}）")

    start, end = content.find("{"), content.rfind("}")
    if start == -1:
        print("未拿到 JSON")
        return
    plan = json.loads(content[start : end + 1])
    print(f"\n标题：{plan.get('title')}")

    resolved, missing, blank = {}, [], 0
    for day in plan["days"]:
        for stop in day["stops"]:
            name = (stop.get("name") or "").strip()
            if not name:
                blank += 1
                continue
            if name in resolved or name in missing:
                continue
            try:
                poi = search_poi(name, CITY)
            except Exception:
                poi = None
            (resolved.setdefault(name, poi) if poi else missing.append(name))

    total = len(resolved) + len(missing)
    print(f"\n—— 存在性：{len(resolved)}/{total}（另有 {blank} 条无对应地点，属正常）")
    for name in missing:
        print(f"   ✗ {name}")

    print("\n—— 地理合理性")
    for day in plan["days"]:
        pts = [resolved[s["name"]] for s in day["stops"] if (s.get("name") or "") in resolved]
        if len(pts) < 2:
            continue
        coords = [{"lat": p.lat, "lng": p.lng} for p in pts]
        spread = max(km(a, b) for i, a in enumerate(coords) for b in coords[i + 1 :])
        bad, warn = SCENARIOS[SCENARIO]["spread_bad"], SCENARIOS[SCENARIO]["spread_warn"]
        flag = "✗ 过于分散" if spread > bad else ("△ 偏大" if spread > warn else "✓")
        print(f"   第{day['day']}天 {len(day['stops'])}站  最远 {spread:5.1f} km  {flag}")

    print("\n—— 搜索带来的实用提示")
    for day in plan["days"]:
        for stop in day["stops"]:
            if stop.get("note"):
                print(f"   {(stop.get('label') or stop.get('name') or '')[:16]:18} {stop['note'][:44]}")

    out = f"/private/tmp/claude-501/-Users-yutongtang-Desktop-Claude/0a3df5f8-4533-4562-82ea-45b340d448a3/scratchpad/plan_{SCENARIO}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
