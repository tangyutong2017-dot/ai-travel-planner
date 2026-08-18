"""编辑 Agent 立项探针：实测「改一次要多久」「模型吐的操作靠不靠谱」。

不改代码库，只打 API。回答三个问题：
1. 一次编辑的时延（生成一次要 60~135 秒，编辑若同量级则功能无意义）
2. 模型能否只吐操作而不重出行程
3. 模型引用的 item_id 是不是真的（编造率）
"""

import json
import os
import time
import urllib.request

ROOT = "/Users/yutongtang/Desktop/Exercise/travel-planner/backend"
for line in open(f"{ROOT}/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

KEY = os.environ["DEEPSEEK_API_KEY"]
BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "apply_edits",
            "description": "对当前行程执行一组编辑操作。只输出需要改动的部分，不要重出整份行程。",
            "parameters": {
                "type": "object",
                "properties": {
                    "ops": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "op": {"type": "string", "enum": ["update", "delete", "insert", "move"]},
                                "day": {"type": "integer", "description": "条目所在天，从 1 开始"},
                                "itemId": {"type": "string", "description": "必须是行程中真实存在的 id"},
                                "title": {"type": "string"},
                                "stopType": {
                                    "type": "string",
                                    "enum": ["sight", "food", "activity", "rest", "flight", "train", "transfer", "hotel"],
                                },
                                "timeSlot": {
                                    "type": "string",
                                    "enum": ["dawn", "morning", "noon", "afternoon", "evening", "night"],
                                },
                                "durationMin": {"type": "integer"},
                                "reason": {"type": "string"},
                                "toDay": {"type": "integer", "description": "move 专用：目标天"},
                                "afterItemId": {"type": "string", "description": "insert/move 专用：插到这个条目之后，留空表示放在当天开头"},
                            },
                            "required": ["op"],
                        },
                    },
                    "reply": {"type": "string", "description": "给用户的一句话说明"},
                },
                "required": ["ops"],
            },
        },
    }
]

SYSTEM = """你是行程编辑助手。用户会用自然语言提出修改要求，你负责把它翻译成编辑操作。

默认执行，不要反问。用户来这里是为了改行程，不是为了回答问题。多问一轮的代价
比选错一个条目的代价更高——选错了用户可以一键撤销。

规则：
- 只调用 apply_edits 输出需要改动的部分，绝不重新输出整份行程。
- itemId 必须从下面给出的行程里原样复制，不得自己编造或改写。
- 有多个条目符合时，按行程顺序选最合理的一个直接执行，并在 reply 里说明你选了哪个、
  以及「如果不是这个可以告诉我」。不要为此反问。
- 位置不明确时自己定：新增条目按时段插到合理位置即可，不要问用户插在第几个。
- 只有一种情况才反问：要求本身无法执行（例如要删的东西行程里根本没有）。
- 新增地点时只给名称，不要编造地址、坐标或价格——系统会去核实。
- reply 用一句话说明你做了什么，不要罗列选项。"""



def slim(trip):
    return {
        "days": [
            {
                "day": d["day"],
                "date": d.get("date"),
                "items": [
                    {
                        "id": i["id"],
                        "title": i["title"],
                        "stopType": i["stopType"],
                        "timeSlot": i["timeSlot"],
                        "durationMin": i["durationMin"],
                    }
                    for i in d["items"]
                ],
            }
            for d in trip["days"]
        ]
    }


def post(body, timeout=120):
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def run(trip, instruction):
    view = slim(trip)
    valid_ids = {i["id"] for d in trip["days"] for i in d["items"]}

    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"当前行程：\n{json.dumps(view, ensure_ascii=False)}\n\n我的要求：{instruction}"},
        ],
        "tools": TOOLS,
        "temperature": 0.3,
    }

    t0 = time.time()
    data = post(body)
    elapsed = time.time() - t0

    msg = data["choices"][0]["message"]
    usage = data.get("usage", {})
    calls = msg.get("tool_calls") or []

    ops, reply, bad_ids = [], msg.get("content") or "", []
    if calls:
        args = json.loads(calls[0]["function"]["arguments"])
        ops = args.get("ops", [])
        reply = args.get("reply", "")
        bad_ids = [o.get("itemId") for o in ops if o.get("itemId") and o["itemId"] not in valid_ids]

    return {
        "instruction": instruction,
        "elapsed": elapsed,
        "in_tok": usage.get("prompt_tokens"),
        "out_tok": usage.get("completion_tokens"),
        "reason_tok": usage.get("completion_tokens_details", {}).get("reasoning_tokens"),
        "called_tool": bool(calls),
        "ops": ops,
        "reply": reply,
        "bad_ids": bad_ids,
    }


CASES = [
    "第二天太赶了，删掉一个景点",
    "把第一天的午饭换成当地特色菜",
    "第二天下午想加一个喝茶的地方",
    "把午饭时间往后挪一点",  # 故意有歧义：两天都有午饭
]

if __name__ == "__main__":
    trip = json.load(open("/tmp/it.json", encoding="utf-8"))
    print(f"行程：{trip['title']}  {len(trip['days'])} 天 / {sum(len(d['items']) for d in trip['days'])} 条目")
    print(f"模型：{MODEL}\n")

    for case in CASES:
        try:
            r = run(trip, case)
        except Exception as exc:  # noqa: BLE001
            print(f"✗ {case}  ->  {type(exc).__name__}: {exc}\n")
            continue

        print(f"【{r['instruction']}】")
        print(f"  耗时 {r['elapsed']:.1f}s   in {r['in_tok']} / out {r['out_tok']} tok (推理 {r['reason_tok']})")
        print(f"  调用工具: {r['called_tool']}   操作数: {len(r['ops'])}   编造 id: {r['bad_ids'] or '无'}")
        for o in r["ops"]:
            print(f"    - {o.get('op'):6} D{o.get('day')} {o.get('itemId') or ''} {o.get('title') or ''}")
        if r["reply"]:
            print(f"  回复: {r['reply'][:100]}")
        print()
