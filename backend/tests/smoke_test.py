"""后端 API 全量冒烟测试。每条断言对应 PRD 里的一项需求。

这些断言验的是 **API 契约与数据流**，不是 AI 质量——后者归 scripts/ 下的
专用脚本管。因此建议让服务带 SKIP_AI_GENERATION=1 启动：

    SKIP_AI_GENERATION=1 .venv/bin/uvicorn app.main:app --port 8000
    python3 backend/tests/smoke_test.py

否则每跑一次都要等一次真实生成（60~135 秒）并消耗 API 额度。
"""
import json
import time
import urllib.parse
import os
import urllib.request
import urllib.error

# 可指向另一个端口，以便在不打断已在运行的开发服务的情况下测新代码
BASE = os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:8000")
results = []


def call(method, path, payload=None):
    req = urllib.request.Request(f"{BASE}{path}", method=method)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {detail}" if detail and not ok else ""))


# --- 健康检查 ---
s, d = call("GET", "/health")
check("health 可用", s == 200 and d.get("status") == "ok", f"{s} {d}")

# --- 创建行程 (PRD 8.1) ---
payload = {
    "originCity": "北京", "destination": "成都",
    "startDate": "2026-10-01", "endDate": "2026-10-03", "days": 3,
    "intercityTransport": "flight",
    "travelers": {"adults": 2, "children": 0, "infants": 0},
    "travelParty": "couple", "visitHistory": "first",
    "preferences": {"interests": ["美食探索", "文化历史"], "pace": "relaxed",
                    "localTransport": ["transit", "walking"], "comfortLevel": "standard",
                    "activityLevel": "medium", "customText": "不吃辣，想慢一点"},
}
s, d = call("POST", "/api/trips", payload)
trip = d.get("tripId")
check("创建行程返回 tripId", s == 200 and bool(trip), f"{s} {d}")

# --- 未生成时取详情应 409 (状态流转) ---
s, d = call("GET", f"/api/trips/{trip}")
check("未生成行程取详情返回 409", s == 409, f"{s} {d}")
check("409 文案为中文", isinstance(d.get("detail"), str) and not d["detail"].isascii(), str(d))

# --- 生成 + 轮询 (PRD 8.2) ---
s, d = call("POST", f"/api/trips/{trip}/generate")
job = d.get("jobId")
check("触发生成返回 jobId", s == 200 and bool(job), f"{s} {d}")

# 真实 agent 要调 LLM、联网搜索、逐个核实地点，实测 60~135 秒。
# 此前占位生成是瞬时的，15 秒的轮询上限一直没暴露问题。
generation_started = time.time()
final = None
for _ in range(90):
    s, d = call("GET", f"/api/jobs/{job}")
    if d.get("status") in ("succeeded", "failed"):
        final = d
        break
    time.sleep(3)
check("生成任务完成", final is not None and final["status"] == "succeeded", str(final))
check("任务返回进度与文案", bool(final) and final.get("progress") == 100 and bool(final.get("message")), str(final))

generation_seconds = time.time() - generation_started
if generation_seconds > 20:
    print(f"\n  提示：本次生成耗时 {generation_seconds:.0f} 秒，服务似乎在跑真实 AI。")
    print("       冒烟测试只需验 API 契约，可用 SKIP_AI_GENERATION=1 启动服务以加速。\n")

# --- 行程详情结构 (PRD 9.2 / 9.3) ---
s, detail = call("GET", f"/api/trips/{trip}")
check("生成后可取详情", s == 200, f"{s} {detail}")
check("天数与创建请求一致", s == 200 and len(detail.get("days", [])) == 3, str(len(detail.get("days", []))))
for field in ("originCity", "route", "travelers", "notes"):
    check(f"Itinerary 含 {field}", field in detail)
check("travelers 为结构而非总数", isinstance(detail.get("travelers"), dict), str(detail.get("travelers")))
d1 = detail["days"][0] if s == 200 and detail.get("days") else {}
for field in ("day", "date", "city", "title", "weather", "stay", "items"):
    check(f"DayPlan 含 {field}", field in d1)
it = d1.get("items", [{}])[0]
for field in ("id", "title", "stopType", "timeSlot", "durationMin", "cost", "verification"):
    check(f"ItineraryItem 含 {field}", field in it)

# --- 手动编辑：改景点 (PRD 8.5 手动编辑) ---
s, d = call("PATCH", f"/api/trips/{trip}/days/1/items/{it['id']}",
            {"title": "宽窄巷子", "timeSlot": "afternoon", "durationMin": 120, "cost": 80})
edited = None
if s == 200:
    edited = next((i for i in d["days"][0]["items"] if i["id"] == it["id"]), None)
check("修改景点成功", s == 200 and edited is not None and edited["title"] == "宽窄巷子", f"{s}")
check("修改后返回完整行程", s == 200 and "days" in d, f"{s}")
check("修改的费用已保存", edited is not None and edited.get("cost") == 80, str(edited))

# --- 手动编辑：删景点 ---
s, d = call("DELETE", f"/api/trips/{trip}/days/1/items/{it['id']}")
check("删除景点成功", s == 200, f"{s} {d}")
check("删除后该项目消失", s == 200 and all(i["id"] != it["id"] for i in d["days"][0]["items"]), "")

# --- 撤销 (编辑 Agent 立项规划 §5) ---
# 上面刚做了「改景点」「删景点」两次编辑，此处应能逐级撤回。
# 这一段同时是路由级的存在性检查：路由函数体里的名字是延迟绑定的，
# 少 import 一个函数时 `import app.main` 照样通过，只有真正打接口才会炸。
s, d = call("GET", f"/api/trips/{trip}/undo")
check("可查撤销状态", s == 200 and d.get("remaining", 0) >= 2, f"{s} {d}")

s, d = call("POST", f"/api/trips/{trip}/undo")
restored = d.get("itinerary") if s == 200 else None
check("撤销删除：条目回来了", s == 200 and restored is not None
      and any(i["id"] == it["id"] for i in restored["days"][0]["items"]), f"{s}")

s, d = call("POST", f"/api/trips/{trip}/undo")
restored = d.get("itinerary") if s == 200 else None
back = next((i for i in restored["days"][0]["items"] if i["id"] == it["id"]), None) if restored else None
check("撤销修改：标题与费用一并还原",
      back is not None and back["title"] != "宽窄巷子" and back.get("cost") != 80, str(back))

s, d = call("GET", f"/api/trips/{trip}/undo")
check("撤尽后 remaining 归零", s == 200 and d.get("remaining") == 0, f"{s} {d}")
s, d = call("POST", f"/api/trips/{trip}/undo")
check("无可撤销时返回 409", s == 409, f"{s} {d}")
s, d = call("POST", "/api/trips/no_such_trip/undo")
check("撤销不存在的行程返回 409", s == 409, f"{s} {d}")

# --- 新增条目：必须过高德核实 (编辑 Agent 立项规划 §3.5b) ---
# 编造的地名不能只是「查不到就拒绝」，更要挡住「匹配到另一个真实地点」——
# 后者带着真实坐标、标着已核实，比直接拒绝更难发现。
s, d = call("POST", f"/api/trips/{trip}/days/1/items",
            {"title": "成都银河洗浴中心旗舰店", "timeSlot": "evening", "stopType": "activity"})
check("编造的地名被拒绝", s == 422, f"{s} {d}")
check("拒绝时说明查的是什么", s == 422 and "成都银河洗浴中心旗舰店" in str(d.get("detail", "")), str(d))

s, d = call("POST", f"/api/trips/{trip}/days/1/items",
            {"title": "宽窄巷子", "timeSlot": "afternoon", "stopType": "sight"})
added = None
if s == 200:
    added = next((i for i in d["days"][0]["items"] if i["title"] == "宽窄巷子"), None)
check("真实地名新增成功", s == 200 and added is not None, f"{s} {d}")
check("新增条目已核实并带坐标",
      added is not None and added["verification"] == "verified" and bool(added.get("location")), str(added))

# 时间线、PDF、地图动线都按数组顺序渲染，插错位置整天顺序就乱了
SLOTS = ["dawn", "morning", "noon", "afternoon", "evening", "night"]
if s == 200:
    seq = [SLOTS.index(i["timeSlot"]) for i in d["days"][0]["items"] if i["timeSlot"] in SLOTS]
    check("新增后当天时段仍单调不减", seq == sorted(seq), str(seq))

s, d = call("POST", f"/api/trips/{trip}/days/99/items",
            {"title": "宽窄巷子", "timeSlot": "afternoon", "stopType": "sight"})
check("往不存在的天新增返回 404", s == 404, f"{s} {d}")

# --- 重命名行程 ---
s, d = call("PATCH", f"/api/trips/{trip}", {"name": "成都三日测试"})
check("重命名行程成功", s == 200 and d.get("name") == "成都三日测试", f"{s} {d}")

# --- 列表 / 筛选 / 排序 / 搜索 (PRD 7.7) ---
s, d = call("GET", "/api/trips")
check("列表返回 items", s == 200 and isinstance(d.get("items"), list), f"{s}")
check("列表返回 summary", s == 200 and isinstance(d.get("summary"), dict), str(d.get("summary")))
check("summary.total 等于 items 长度", d.get("summary", {}).get("total") == len(d.get("items", [])), "")

s, f1 = call("GET", "/api/trips?status=planned")
check("按 planned 筛选", s == 200 and all(t["status"] == "planned" for t in f1["items"]), f"{s}")
s, f2 = call("GET", "/api/trips?status=completed")
check("按 completed 筛选", s == 200 and all(t["status"] == "completed" for t in f2["items"]), f"{s}")
s, f3 = call("GET", "/api/trips?keyword=" + urllib.parse.quote("成都"))
check("关键词搜索", s == 200 and all("成都" in t["name"] or "成都" in t["dest"] for t in f3["items"]), f"{s}")
for mode in ("updatedAt_desc", "startDate_desc", "days_desc"):
    s, _ = call("GET", f"/api/trips?sort={mode}")
    check(f"排序 {mode} 可用", s == 200, str(s))
s, srt = call("GET", "/api/trips?sort=days_desc")
days_list = [t["days"] for t in srt["items"]]
check("days_desc 真的按天数降序", days_list == sorted(days_list, reverse=True), str(days_list))

# --- 错误分支 ---
s, d = call("GET", "/api/trips/no_such_trip")
check("不存在的行程返回 404", s == 404, f"{s} {d}")
s, d = call("GET", "/api/jobs/no_such_job")
check("不存在的任务返回 404", s == 404, f"{s} {d}")
s, d = call("DELETE", "/api/trips/no_such_trip")
check("删除不存在的行程返回 404", s == 404, f"{s} {d}")
s, d = call("PATCH", f"/api/trips/{trip}/days/9/items/nope", {"title": "x"})
check("修改不存在的项目返回 404", s == 404, f"{s} {d}")
s, d = call("POST", "/api/trips", {"destination": "只有目的地"})
check("创建行程缺字段返回 422", s == 422, f"{s}")

# --- 清理 ---
s, _ = call("DELETE", f"/api/trips/{trip}")
check("删除测试行程", s == 200, str(s))

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n{'=' * 46}\n通过 {passed}/{len(results)}")
for name, ok, detail in results:
    if not ok:
        print(f"  失败: {name}  {detail}")
