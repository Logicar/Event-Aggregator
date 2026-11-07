"""导出：生成 events.json（活动 Feed）与 archive.json（归档 Feed）。"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List

from zoneinfo import ZoneInfo

from .models import Event, DOMAIN_VALUES, TYPE_VALUES, STATUS_VALUES, MATERIAL_TYPE_VALUES, SOURCE_TYPE_VALUES

TZ = ZoneInfo("Asia/Shanghai")


def _now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def validate(event_dict: dict) -> List[str]:
    """轻量校验（无需 jsonschema），返回错误信息列表。"""
    errors: List[str] = []
    required = [
        "id", "title", "type", "domains", "province", "city", "venue",
        "start_date", "end_date", "url", "source_url", "source_name", "source_type", "status",
    ]
    for key in required:
        if key not in event_dict or event_dict[key] in (None, "", []):
            errors.append(f"缺少必填字段或为空: {key}")
    if event_dict.get("type") not in TYPE_VALUES:
        errors.append(f"非法 type: {event_dict.get('type')}")
    if event_dict.get("status") not in STATUS_VALUES:
        errors.append(f"非法 status: {event_dict.get('status')}")
    if event_dict.get("source_type") not in SOURCE_TYPE_VALUES:
        errors.append(f"非法 source_type: {event_dict.get('source_type')}")
    domains = event_dict.get("domains") or []
    for d in domains:
        if d not in DOMAIN_VALUES:
            errors.append(f"非法 domain: {d}")
    for m in event_dict.get("materials") or []:
        if m.get("type") not in MATERIAL_TYPE_VALUES:
            errors.append(f"非法 material.type: {m.get('type')}")
    return errors


def _envelope(events: List[Event]) -> dict:
    payload = [e.to_dict() for e in events]
    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "count": len(payload),
        "events": payload,
    }


def export(active: List[Event], archived: List[Event], out_dir: str) -> dict:
    """写出 data/events.json 与 data/archive.json，返回校验统计。"""
    os.makedirs(out_dir, exist_ok=True)

    active_env = _envelope(active)
    archive_env = _envelope(archived)

    invalid = 0
    for env, path in ((active_env, "events.json"), (archive_env, "archive.json")):
        for ev in env["events"]:
            errs = validate(ev)
            if errs:
                invalid += 1
                print(f"[校验失败] {ev.get('id')}: {errs}")

    events_path = os.path.join(out_dir, "events.json")
    archive_path = os.path.join(out_dir, "archive.json")
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(active_env, f, ensure_ascii=False, indent=2)
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive_env, f, ensure_ascii=False, indent=2)

    return {
        "active_count": len(active),
        "archive_count": len(archived),
        "invalid_count": invalid,
        "events_path": events_path,
        "archive_path": archive_path,
    }
