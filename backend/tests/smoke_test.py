"""后端 API 全量冒烟测试。每条断言对应 PRD 里的一项需求。"""
import json
import time
import urllib.parse
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
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

final = None
for _ in range(30):
    s, d = call("GET", f"/api/jobs/{job}")
    if d.get("status") in ("succeeded", "failed"):
        final = d
        break
    time.sleep(0.5)
check("生成任务完成", final is not None and final["status"] == "succeeded", str(final))
check("任务返回进度与文案", bool(final) and final.get("progress") == 100 and bool(final.get("message")), str(final))

# --- 行程详情结构 (PRD 9.2 / 9.3) ---
s, detail = call("GET", f"/api/trips/{trip}")
check("生成后可取详情", s == 200, f"{s} {detail}")
check("天数与创建请求一致", s == 200 and len(detail.get("days", [])) == 3, str(len(detail.get("days", []))))
for field in ("originCity", "route", "travelers", "notes", "bookings"):
    check(f"Itinerary 含 {field}", field in detail)
check("travelers 为结构而非总数", isinstance(detail.get("travelers"), dict), str(detail.get("travelers")))
d1 = detail["days"][0] if s == 200 and detail.get("days") else {}
for field in ("day", "date", "city", "title", "weather", "stay", "items"):
    check(f"DayPlan 含 {field}", field in d1)
it = d1.get("items", [{}])[0]
for field in ("id", "title", "stopType", "startTime", "durationMin", "cost", "verification"):
    check(f"ItineraryItem 含 {field}", field in it)

# --- 手动编辑：改景点 (PRD 8.5 手动编辑) ---
s, d = call("PATCH", f"/api/trips/{trip}/days/1/items/{it['id']}",
            {"title": "宽窄巷子", "startTime": "10:00", "durationMin": 120, "cost": 80})
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
