"""端到端测对话编辑：一句话改行程，看时延、回执、落位、撤销。"""

import json
import time
import urllib.error
import urllib.request

BASE = "http://localhost:8001"
TRIP = "trip_new_34acbfa2"
SLOTS = ["dawn", "morning", "noon", "afternoon", "evening", "night"]


def call(method, path, payload=None, timeout=90):
    req = urllib.request.Request(f"{BASE}{path}", method=method)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def snapshot():
    _, d = call("GET", f"/api/trips/{TRIP}")
    return [[i["title"] for i in day["items"]] for day in d["days"]]


def slots_ok(itinerary):
    for day in itinerary["days"]:
        seq = [SLOTS.index(i["timeSlot"]) for i in day["items"] if i["timeSlot"] in SLOTS]
        if seq != sorted(seq):
            return False, f"D{day['day']} {seq}"
    return True, ""


def chat(message):
    t0 = time.time()
    s, d = call("POST", f"/api/trips/{TRIP}/chat", {"message": message})
    elapsed = time.time() - t0
    print(f"\n【{message}】  {elapsed:.1f}s  HTTP {s}")
    if s != 200:
        print(f"   拒绝：{d.get('detail')}")
        return s, d
    print(f"   回执(代码生成): {d['changes'] or '（无操作）'}")
    print(f"   模型的话       : {d['reply'][:70]}")
    print(f"   改动条目 id    : {len(d['changedItemIds'])} 个   可撤销 {d['undoRemaining']}")
    if d.get("itinerary"):
        ok, why = slots_ok(d["itinerary"])
        print(f"   时段单调不减   : {'✅' if ok else '❌ ' + why}")
    return s, d


before = snapshot()
print("改动前：")
for n, titles in enumerate(before, 1):
    print(f"  D{n}: " + " / ".join(t[:14] for t in titles))

chat("第二天太赶了，删掉一个景点")
chat("第一天下午加个婺源博物馆")
chat("把第一天的午饭时间改成 1 小时")
chat("在第二天加一个叫「星空观景茶室」的地方")   # 编造地名，应被拒
chat("把第五天的行程删掉")                      # 不存在的天，应被拒

print("\n改动后：")
for n, titles in enumerate(snapshot(), 1):
    print(f"  D{n}: " + " / ".join(t[:14] for t in titles))

print("\n逐次撤销：")
for i in range(10):
    s, d = call("POST", f"/api/trips/{TRIP}/undo")
    if s != 200:
        print(f"  第 {i+1} 次 -> HTTP {s}（撤尽）")
        break
    print(f"  第 {i+1} 次 -> 剩余 {d['remaining']}")

after = snapshot()
print("\n撤销后：")
for n, titles in enumerate(after, 1):
    print(f"  D{n}: " + " / ".join(t[:14] for t in titles))
print("\n是否完全还原:", "✅" if after == before else "❌ 与初始不一致")
