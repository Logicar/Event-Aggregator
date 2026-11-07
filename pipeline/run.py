"""管道编排入口：抓取 → 清洗 → 去重 → 状态判定 → 归档拆分 → 导出。

用法：
    python -m pipeline.run --demo
    python -m pipeline.run --config sources/sources.yaml --out data
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from .archive import archive_event
from .dedup import dedup, make_id
from .demo import load_demo_events
from .export import export
from .models import Event
from .normalize import today_str
from .status import split_active_archive


def _finalize_ids(events: List[Event]) -> None:
    for ev in events:
        if not ev.id or ev.id.startswith("demo-"):
            ev.id = make_id(ev)


def run_demo(out_dir: str) -> None:
    events = load_demo_events()
    _finalize_ids(events)
    run_pipeline(events, out_dir)


def run_from_config(config_path: str, out_dir: str) -> None:
    """从 sources.yaml 抓取真实数据源。需要 PyYAML + 抓取引擎。"""
    try:
        from scrapers.engine import scrape_all
    except ImportError as exc:  # pragma: no cover
        print(f"抓取引擎不可用：{exc}")
        print("提示：真实抓取需先 `pip install -r requirements.txt`。")
        sys.exit(1)

    events = scrape_all(config_path)
    if not events:
        print("[pipeline] 未抓取到任何活动，保留现有数据文件不变（避免清空数据）。")
        return
    run_pipeline(events, out_dir)


def run_pipeline(events: List[Event], out_dir: str) -> None:
    today = today_str()
    print(f"[pipeline] 当天 = {today}，输入 {len(events)} 条")

    # 去重（生成稳定 id）
    deduped = dedup(events)
    _finalize_ids(deduped)
    print(f"[pipeline] 去重后 {len(deduped)} 条")

    # 状态判定 + 归档拆分
    active, archived = split_active_archive(deduped, today)
    for ev in archived:
        archive_event(ev)
    print(f"[pipeline] 活动 Feed {len(active)} 条 / 归档 Feed {len(archived)} 条")

    # 导出
    result = export(active, archived, out_dir)
    print(
        f"[pipeline] 已写出 {result['events_path']}（{result['active_count']} 条）、"
        f"{result['archive_path']}（{result['archive_count']} 条），"
        f"校验失败 {result['invalid_count']} 条"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="会议论坛信息聚合管道")
    parser.add_argument("--demo", action="store_true", help="使用演示数据跑通全流程")
    parser.add_argument("--config", default="sources/sources.yaml", help="数据源配置文件")
    parser.add_argument("--out", default="data", help="输出目录")
    args = parser.parse_args(argv)

    if args.demo:
        run_demo(args.out)
    else:
        run_from_config(args.config, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
