"""行程编辑的快照与撤销。

设计见 `docs/编辑Agent立项规划-v0.1.md` 第 5 节。三条语义：

1. **一条指令 = 一份快照**，不是一个操作一份。用户说「删掉两个景点」产生两个删除操作，
   撤销时期望撤销的是这句话。因此多操作的调用方必须在内存里改完再存一次，
   而不是每个操作各存一次。
2. **手动编辑也快照。** 否则会有这个陷阱：AI 改一次 → 手动改一次 → 点撤销 →
   手动那次被静默抹掉，用户完全无法预期。
3. **撤销不可再撤销。** 不做重做栈，被消费的快照直接删除。
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import Itinerary
from ..orm_models import ItineraryRecord, ItineraryRevisionRecord


# 只能撤一步的话，连改三次才发现第一次错了就没救了——这是常见场景。
# 一份快照约 5.5KB，留十份的代价可以忽略。
MAX_REVISIONS_PER_TRIP = 10


def snapshot_itinerary(db: Session, trip_id: str, label: str) -> None:
    """在覆写前记下当前 days_json。没有既有行程时什么也不做（无可撤销之物）。

    只入 session 不提交，由调用方的事务一并提交——否则写入成功而快照失败时，
    会留下一份指向错误状态的撤销点。
    """
    record = db.get(ItineraryRecord, trip_id)
    if not record or not record.days_json:
        return

    db.add(
        ItineraryRevisionRecord(
            trip_id=trip_id,
            days_json=record.days_json,
            label=label[:120],
        )
    )

    # 超出上限的旧快照直接丢弃。按 id 排序而非 created_at——
    # 同一秒内的多次编辑用时间戳分不出先后。
    keep_ids = db.scalars(
        select(ItineraryRevisionRecord.id)
        .where(ItineraryRevisionRecord.trip_id == trip_id)
        .order_by(ItineraryRevisionRecord.id.desc())
        .limit(MAX_REVISIONS_PER_TRIP - 1)
    ).all()

    stale = delete(ItineraryRevisionRecord).where(ItineraryRevisionRecord.trip_id == trip_id)
    if keep_ids:
        stale = stale.where(ItineraryRevisionRecord.id.notin_(keep_ids))
    db.execute(stale)


def latest_revision(db: Session, trip_id: str) -> ItineraryRevisionRecord | None:
    return db.scalars(
        select(ItineraryRevisionRecord)
        .where(ItineraryRevisionRecord.trip_id == trip_id)
        .order_by(ItineraryRevisionRecord.id.desc())
        .limit(1)
    ).first()


def undo_count(db: Session, trip_id: str) -> int:
    """还能撤几步。前端据此决定撤销按钮是否可用。"""
    return len(
        db.scalars(select(ItineraryRevisionRecord.id).where(ItineraryRevisionRecord.trip_id == trip_id)).all()
    )


def undo_last_edit(db: Session, trip_id: str) -> Itinerary | None:
    """回到上一份快照。没有可撤销的改动时返回 None。"""
    from .itineraries import get_itinerary, save_itinerary

    revision = latest_revision(db, trip_id)
    if not revision:
        return None

    current = get_itinerary(db, trip_id)
    if not current:
        return None

    # 过 model_validate 而不是 model_copy：后者不做校验，历史快照若是旧结构
    # 会带着脏数据一路写回库里，等到渲染时才炸。
    restored = Itinerary.model_validate({**current.model_dump(), "days": revision.days_json})

    # 撤销本身不留快照，否则反复点撤销会在两个状态间来回横跳。
    save_itinerary(db, trip_id, restored, snapshot_label=None, commit=False)
    db.delete(revision)
    db.commit()
    return restored
