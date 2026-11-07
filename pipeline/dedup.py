"""去重：URL+标题指纹，跨来源/跨平台合并。"""
from __future__ import annotations

import hashlib
from typing import List

from .models import Event


def fingerprint(ev: Event) -> str:
    """基于标题+起止日期的稳定指纹（与来源解耦，便于跨平台合并）。"""
    key = f"{ev.title.strip()}|{ev.start_date}|{ev.end_date}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def make_id(ev: Event) -> str:
    """生成稳定唯一 ID：evt_<开始日期>_<指纹>。"""
    date_part = (ev.start_date or "00000000").replace("-", "")
    return f"evt_{date_part}_{fingerprint(ev)}"


def _merge(base: Event, incoming: Event) -> None:
    """将 incoming 的补充信息合并进 base（保留更完整的字段）。"""
    base.fields = sorted(set(base.fields) | set(incoming.fields))
    base.keywords = sorted(set(base.keywords) | set(incoming.keywords))
    base.tags = sorted(set(base.tags) | set(incoming.tags))
    base.registration_requirements = sorted(
        set(base.registration_requirements) | set(incoming.registration_requirements)
    )
    base.materials = _merge_materials(base.materials, incoming.materials)
    for attr in (
        "organizer", "institution", "organizer_type",
        "registration_url", "registration_deadline", "abstract_deadline", "summary",
    ):
        if not getattr(base, attr) and getattr(incoming, attr):
            setattr(base, attr, getattr(incoming, attr))
    # 来源优先级：website > rss > 平台 > manual
    if _source_rank(incoming.source_type) > _source_rank(base.source_type):
        base.source_name = incoming.source_name
        base.source_type = incoming.source_type
        base.source_url = incoming.source_url


def _source_rank(t: str) -> int:
    return {"website": 5, "rss": 4, "wechat_mp": 3, "xiaohongshu": 2, "douyin": 1, "manual": 0}.get(t, 0)


def _merge_materials(a, b):
    seen = {(m["url"]) for m in a}
    merged = list(a)
    for m in b:
        if m["url"] not in seen:
            merged.append(m)
            seen.add(m["url"])
    return merged


def dedup(events: List[Event]) -> List[Event]:
    """按指纹去重并合并重复项，返回去重后的列表（保序）。"""
    seen = {}
    order: List[str] = []
    for ev in events:
        fp = fingerprint(ev)
        if fp in seen:
            _merge(seen[fp], ev)
        else:
            seen[fp] = ev
            order.append(fp)
    return [seen[fp] for fp in order]
