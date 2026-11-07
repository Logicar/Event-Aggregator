"""Event 数据模型：活动与归档共用同一结构。"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

DOMAIN_VALUES = {"生命科学", "医学药学", "AI4Science"}
TYPE_VALUES = {"conference", "forum", "lecture", "seminar", "workshop"}
STATUS_VALUES = {"upcoming", "ongoing", "ended"}
MATERIAL_TYPE_VALUES = {"video", "slides", "document", "minutes", "summary"}
SOURCE_TYPE_VALUES = {"website", "wechat_mp", "xiaohongshu", "douyin", "rss", "manual"}


@dataclass
class Event:
    """一条会议/论坛/讲座活动记录。"""

    id: str
    title: str
    type: str
    domains: List[str]
    province: str
    city: str
    venue: str
    start_date: str
    end_date: str
    url: str
    source_url: str
    source_name: str
    source_type: str
    status: str
    fields: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    organizer: Optional[str] = None
    institution: Optional[str] = None
    organizer_type: Optional[str] = None
    registration_url: Optional[str] = None
    registration_deadline: Optional[str] = None
    registration_requirements: List[str] = field(default_factory=list)
    abstract_deadline: Optional[str] = None
    summary: Optional[str] = None
    materials: List[Dict[str, str]] = field(default_factory=list)
    first_seen: Optional[str] = None
    last_updated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典，丢弃值为 None 的可选字段，保证 JSON 干净。"""
        data: Dict[str, Any] = {}
        for key, value in asdict(self).items():
            if value is None:
                continue
            data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
