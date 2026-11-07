"""清洗与归一化：中文日期/区间、地域、报名条件条目化。"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")

# ── 日期解析 ────────────────────────────────────────────────

_DATE_RE = re.compile(r"(?P<y>\d{4})\s*[年./\-]\s*(?P<m>\d{1,2})\s*[月./\-]\s*(?P<d>\d{1,2})\s*日?")
_YEAR_MONTH_RE = re.compile(r"(?P<y>\d{4})\s*[年./\-]\s*(?P<m>\d{1,2})\s*月")


def today_str() -> str:
    return datetime.now(TZ).date().isoformat()


def _pad(v: str) -> str:
    return v.zfill(2)


def parse_date(text: Optional[str]) -> Optional[str]:
    """解析单个日期为 ISO 字符串（YYYY-MM-DD）。无法解析返回 None。"""
    if not text:
        return None
    m = _DATE_RE.search(str(text))
    if not m:
        return None
    y, mo, d = int(m.group("y")), int(m.group("m")), int(m.group("d"))
    try:
        return datetime(y, mo, d).date().isoformat()
    except ValueError:
        return None


def parse_date_range(text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """解析起止日期，支持 `2026年7月1日-4日`、`2026-07-01 至 07-04` 等。

    返回 (start, end) ISO 字符串；缺失时对应项为 None。
    """
    if not text:
        return None, None
    s = str(text).strip()

    # 情况一：两个完整日期 `2026年7月1日 至 2026年7月4日` / `2026-07-01~2026-07-04`
    dates = _DATE_RE.findall(s)
    if len(dates) >= 2:
        start = parse_date(s)  # 取第一个
        # 取最后一个完整日期
        last_m = None
        for mm in _DATE_RE.finditer(s):
            last_m = mm
        end = _build_date(last_m.group("y"), last_m.group("m"), last_m.group("d"))
        return start, end

    # 情况二：同月跨日 `2026年7月1日-4日`（第二个日期省略年月）
    m = re.search(
        r"(?P<y>\d{4})\s*[年./\-]\s*(?P<m>\d{1,2})\s*[月./\-]\s*(?P<d1>\d{1,2})\s*日?\s*[—\-~至到]\s*(?P<d2>\d{1,2})\s*日?",
        s,
    )
    if m:
        start = _build_date(m.group("y"), m.group("m"), m.group("d1"))
        end = _build_date(m.group("y"), m.group("m"), m.group("d2"))
        return start, end

    # 情况三：单个完整日期
    single = parse_date(s)
    if single:
        return single, single

    return None, None


def _build_date(y: str, m: str, d: str) -> Optional[str]:
    try:
        return datetime(int(y), int(m), int(d)).date().isoformat()
    except ValueError:
        return None


# ── 地域归一化 ──────────────────────────────────────────────

# 常见别名 → 规范省市
_REGION_ALIASES = {
    "北京": ("北京", "北京"),
    "北京市": ("北京", "北京"),
    "上海": ("上海", "上海"),
    "上海市": ("上海", "上海"),
    "广州": ("广东", "广州"),
    "深圳": ("广东", "深圳"),
    "杭州": ("浙江", "杭州"),
    "南京": ("江苏", "南京"),
    "武汉": ("湖北", "武汉"),
    "成都": ("四川", "成都"),
    "西安": ("陕西", "西安"),
    "长沙": ("湖南", "长沙"),
    "苏州": ("江苏", "苏州"),
}


def normalize_region(province: str, city: str) -> Tuple[str, str]:
    """将省市字符串归一化为规范值，能推断时补全省份。"""
    p, c = (province or "").strip(), (city or "").strip()
    for alias, (np, nc) in _REGION_ALIASES.items():
        if alias in (p, c):
            return np, nc
    if not p and c:
        return c, c  # 无法判断省份时以城市兜底
    return (p or "线上"), (c or "线上")


# ── 报名条件条目化 ──────────────────────────────────────────

def split_requirements(text: Optional[str]) -> List[str]:
    """将报名条件原文归纳为清晰条目（按换行/分号/顿号切分）。"""
    if not text:
        return []
    s = str(text).strip()
    # 优先按换行、分号、句号切分
    parts = re.split(r"[\n\r;；。]+", s)
    items = [p.strip(" ，,、") for p in parts if p.strip(" ，,、")]
    return [i for i in items if i]
