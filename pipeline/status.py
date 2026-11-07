"""状态判定 + 归档拆分：以北京时间“当天”为界。"""
from __future__ import annotations

from datetime import date
from typing import List, Tuple

from .models import Event
from .normalize import today_str


def determine_status(start_date: str, end_date: str, today: str) -> str:
    """依据当天判定状态：
    - end_date < 当天   → ended（已结束，转入归档）
    - start_date ≤ 当天 ≤ end_date → ongoing（进行中）
    - 否则             → upcoming（未开始）
    """
    t = date.fromisoformat(today)
    s = date.fromisoformat(start_date) if start_date else None
    e = date.fromisoformat(end_date) if end_date else None

    if s is None or e is None:
        # 时间缺失：保守判为 upcoming，交由人工复核队列处理
        return "upcoming"
    if e < t:
        return "ended"
    if s <= t <= e:
        return "ongoing"
    return "upcoming"


def split_active_archive(events: List[Event], today: str) -> Tuple[List[Event], List[Event]]:
    """将活动拆分为活动 Feed（upcoming/ongoing）与归档 Feed（ended）。

    同时回写 status 字段。
    """
    active: List[Event] = []
    archived: List[Event] = []
    for ev in events:
        ev.status = determine_status(ev.start_date, ev.end_date, today)
        if ev.status == "ended":
            archived.append(ev)
        else:
            active.append(ev)
    return active, archived
