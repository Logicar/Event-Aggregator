"""归档：为已结束活动整理资料（回放视频/文档/PPT/纪要/总结）。"""
from __future__ import annotations

from typing import List

from .models import Event


def collect_materials(ev: Event) -> List[dict]:
    """采集/归纳归档资料。

    当前实现：若活动已带 materials 则原样返回；
    否则以原文链接作为兜底「原文/回顾」入口，标记待补资料。
    后续可在实施阶段接入会后回顾页解析补充视频/文档链接。
    """
    if ev.materials:
        return ev.materials
    return [
        {
            "type": "summary",
            "title": "原文/回顾入口",
            "url": ev.url,
        }
    ]


def archive_event(ev: Event) -> Event:
    """对已结束活动补齐归档资料。"""
    ev.materials = collect_materials(ev)
    return ev
