"""各站点专用抓取器：列表 + 详情页解析（时间/地点/主办方）。"""
from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urljoin

from pipeline.models import Event
from pipeline.normalize import parse_date_range

# 常见城市 → 省份
CITY_PROVINCE = {
    "北京": "北京", "上海": "上海", "天津": "天津", "重庆": "重庆",
    "杭州": "浙江", "南京": "江苏", "苏州": "江苏", "无锡": "江苏", "常州": "江苏", "南通": "江苏",
    "武汉": "湖北", "成都": "四川", "广州": "广东", "深圳": "广东", "珠海": "广东", "佛山": "广东",
    "西安": "陕西", "长沙": "湖南", "昆明": "云南", "南昌": "江西", "银川": "宁夏", "合肥": "安徽",
    "郑州": "河南", "济南": "山东", "青岛": "山东", "沈阳": "辽宁", "大连": "辽宁",
    "哈尔滨": "黑龙江", "长春": "吉林", "石家庄": "河北", "太原": "山西", "福州": "福建", "厦门": "福建",
    "贵阳": "贵州", "南宁": "广西", "海口": "海南", "兰州": "甘肃", "西宁": "青海",
    "乌鲁木齐": "新疆", "呼和浩特": "内蒙古", "拉萨": "西藏", "温州": "浙江", "宁波": "浙江",
}

# 会议相关标题关键词（用于过滤非会议类公告）
CONFERENCE_KW = re.compile(r"会议|大会|年会|论坛|研讨|讲座|沙龙|培训|研修|药师周")


def strip_html(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&ldquo;", "\u201c").replace("&rdquo;", "\u201d")
                .replace("&middot;", "\u00b7"))
    return re.sub(r"\s+", " ", html).strip()


def infer_region(text: str) -> tuple:
    """从文本推断 (province, city)，取文本中最早出现的已知城市。"""
    if not text:
        return "待确认", "待确认"
    best_pos: Optional[int] = None
    best: Optional[tuple] = None
    for city, prov in CITY_PROVINCE.items():
        pos = text.find(city)
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos = pos
            best = (prov, city)
    return best if best else ("待确认", "待确认")


def extract_date(text: str) -> tuple:
    """从正文提取会议日期，返回 (start, end) ISO。"""
    # 排除「发布时间/报名时间/注册时间」等，只匹配「会议时间/时间」
    m = re.search(
        r"(?<!发布)(?<!报名)(?<!注册)(?<!投稿)(?<!摘要)(?<!报到)"
        r"时间[：:]\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日[^，。；\s]{0,14})",
        text,
    )
    if m:
        return parse_date_range(m.group(1))
    # 兜底：找正文里第一个「2026年X月X日」日期
    m2 = re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日[^，。；\s]{0,14}", text)
    if m2:
        return parse_date_range(m2.group(0))
    return None, None


def extract_venue(text: str) -> Optional[str]:
    m = re.search(r"(?:会议|举办|报到)?地点[：:]\s*([^\s，。；；]{2,80})", text)
    return m.group(1).strip(" ，。；、") if m else None


def extract_organizer(text: str, default: Optional[str] = None) -> Optional[str]:
    m = re.search(r"主办单位[：:]\s*([^\s，。；；]{2,60})", text)
    return m.group(1).strip(" ，。；、") if m else default


def build_event(source: dict, list_url: str, title: str, detail_url: str,
                start: Optional[str], end: Optional[str], venue: Optional[str],
                organizer: Optional[str], body_text: str = "") -> Event:
    # 优先级：venue → 标题 → 正文（避免正文里的学会地址城市污染）
    province, city = "待确认", "待确认"
    for t in (venue, title, body_text):
        if t:
            p, c = infer_region(t)
            if c != "待确认":
                province, city = p, c
                break
    return Event(
        id="",
        title=title.strip(),
        type="conference",
        domains=list(source.get("domains", [])),
        fields=list(source.get("fields", [])),
        organizer=organizer,
        institution=organizer,
        organizer_type=source.get("organizer_type") or "society",
        province=province,
        city=city,
        venue=venue or "待确认",
        start_date=start or "",
        end_date=end or "",
        registration_url=detail_url,
        url=detail_url,
        source_url=list_url,
        source_name=source.get("name", ""),
        source_type="website",
        status="upcoming",
    )


# ── 中国药学会 ─────────────────────────────────────────────
def scrape_cpa(source: dict, client) -> List[Event]:
    base = "https://www.cpa.org.cn/"
    list_url = source["list_url"]
    events: List[Event] = []
    res = client.get(list_url)
    if not res:
        return events

    # 列表项：<li><a href="?do=info&cid=X" title="...">标题</a><span>日期</span></li>
    items = re.findall(
        r'<a href="([^"]*do=info&cid=\d+[^"]*)"[^>]*(?:title="([^"]*)")?[^>]*>(.*?)</a>',
        res.html, re.S | re.I,
    )
    seen = set()
    for href, title_attr, inner in items:
        title = title_attr or re.sub(r"<[^>]+>", "", inner).strip()
        title = re.sub(r"\s+", "", title)
        if not title or not CONFERENCE_KW.search(title):
            continue
        if href in seen:
            continue
        seen.add(href)
        detail_url = urljoin(base, href.replace("&amp;", "&"))
        detail = client.get(detail_url)
        text = strip_html(detail.html) if detail else ""
        start, end = extract_date(text)
        if not start:
            continue
        venue = extract_venue(text)
        organizer = extract_organizer(text, "中国药学会")
        events.append(build_event(source, list_url, title, detail_url, start, end, venue, organizer, body_text=text))
        if len(events) >= 12:
            break
    return events


# ── 中国人工智能学会 ───────────────────────────────────────
def scrape_caai(source: dict, client) -> List[Event]:
    base = "https://www.caai.cn"
    list_url = source["list_url"]
    events: List[Event] = []
    res = client.get(list_url)
    if not res:
        return events

    # 列表项：• 标题 [置顶] 日期 -> /site/content/X.html
    items = re.findall(
        r'<a[^>]+href="(/site/content/\d+\.html)"[^>]*>(.*?)</a>',
        res.html, re.S | re.I,
    )
    seen = set()
    for href, inner in items:
        title = re.sub(r"<[^>]+>", "", inner)
        title = re.sub(r"\s+", " ", title).replace("•", "").strip()
        title = re.sub(r"\s*\d{4}-\d{2}-\d{2}\s*$", "", title)  # 去掉尾部发布日期
        title = re.sub(r"\s*置顶\s*", "", title).strip()
        if not title or not CONFERENCE_KW.search(title):
            continue
        if href in seen:
            continue
        seen.add(href)
        detail_url = urljoin(base, href)
        detail = client.get(detail_url)
        text = strip_html(detail.html) if detail else ""
        start, end = extract_date(text)
        if not start:
            continue
        venue = extract_venue(text)
        organizer = extract_organizer(text, "中国人工智能学会")
        events.append(build_event(source, list_url, title, detail_url, start, end, venue, organizer, body_text=text))
        if len(events) >= 12:
            break
    return events


ADAPTERS = {
    "cpa": scrape_cpa,
    "caai": scrape_caai,
}
