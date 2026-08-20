"""为 insert 选相似度阈值：测真实地名与编造地名的分数分布，找可分点。

生成路径要的是召回（宁可宽松也别漏），insert 要的是准确（宁可拒绝也别指错地方）。
所以不改 resolve_place，只在 insert 侧加一道更严的校验——阈值由数据定。
"""

import sys

sys.path.insert(0, "/Users/yutongtang/Desktop/Exercise/travel-planner/backend")

from app.generation import destination_center, match_score, resolve_place  # noqa: E402

DEST = "婺源"

# 真实存在的地方，含 LLM 常见的「名称 · 描述」写法
REAL = [
    "李坑", "篁岭", "江湾", "汪口", "婺源博物馆", "思溪延村", "彩虹桥", "月亮湾",
    "晓起村", "严田古樟民俗园", "婺源站", "рrite",  # 最后一个是乱码对照
]
# 编造的地方
FAKE = [
    "婺源星空观景茶室", "婺源银河洗浴中心", "婺源麦当劳旗舰店", "汪口茶馆",
    "下午茶歇", "婺源云顶温泉会所", "李坑观景咖啡屋", "婺源国际会展中心",
]

center = destination_center(DEST)


def score_of(name):
    poi = resolve_place(name, DEST, DEST, center)
    if not poi:
        return None, None
    return match_score(name, poi), poi.name


print(f"{'地名':<22} {'分数':>6}  匹配到")
print("-" * 70)
real_scores, fake_scores = [], []
for label, names, bucket in (("真实", REAL, real_scores), ("编造", FAKE, fake_scores)):
    print(f"\n[{label}]")
    for name in names:
        score, matched = score_of(name)
        if score is None:
            print(f"  {name:<20} {'拒绝':>6}")
            continue
        bucket.append(score)
        print(f"  {name:<20} {score:>6.2f}  {matched[:26]}")

if real_scores and fake_scores:
    print("\n" + "=" * 70)
    print(f"真实：最低 {min(real_scores):.2f}  中位附近 {sorted(real_scores)[len(real_scores)//2]:.2f}")
    print(f"编造：最高 {max(fake_scores):.2f}")
    gap = min(real_scores) - max(fake_scores)
    print(f"可分间隔 {gap:+.2f}" + ("  → 存在干净的分界" if gap > 0 else "  → 有重叠，阈值必然误伤或漏放"))
