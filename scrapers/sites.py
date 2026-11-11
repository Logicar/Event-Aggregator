"""各站点专用抓取器：列表 + 详情页解析（时间/地点/主办方）。"""
from __future__ import annotations

import calendar
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


PROVINCE_NAMES = [
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
    "广东", "广西", "海南", "四川", "贵州", "云南", "西藏", "陕西", "甘肃",
    "青海", "宁夏", "新疆", "内蒙古",
]


def infer_region(text: str) -> tuple:
    """从文本推断 (province, city)，取文本中最早出现的已知城市；无城市时回退到省份。"""
    if not text:
        return "待确认", "待确认"
    best_pos: Optional[int] = None
    best: Optional[tuple] = None
    for city, prov in CITY_PROVINCE.items():
        pos = text.find(city)
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos = pos
            best = (prov, city)
    if best:
        return best
    # 无已知城市，尝试省名（如「江西省」）
    for p in PROVINCE_NAMES:
        if (p + "省") in text or (p + "市") in text:
            return p, "待确认"
    return "待确认", "待确认"


def extract_date(text: str) -> tuple:
    """从正文提取会议日期，返回 (start, end) ISO。"""
    # 1) 会议时间/时间（排除 发布/报名/注册/投稿/摘要/报到），支持 17-20 日期范围
    m = re.search(
        r"(?<!发布)(?<!报名)(?<!注册)(?<!投稿)(?<!摘要)(?<!报到)"
        r"时间\s*[：:]\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?[^。；\n]{0,20})",
        text,
    )
    if m:
        return parse_date_range(m.group(1))
    # 2) 定于/将于/拟于 + 日期
    m2 = re.search(r"(?:定于|将于|拟于)\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?[^。；\n]{0,20})", text)
    if m2:
        return parse_date_range(m2.group(1))
    # 3) 兜底：第一个完整日期（含范围）
    m3 = re.search(r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?(?:\s*[-~至—]\s*\d{1,2}\s*日)?", text)
    if m3:
        return parse_date_range(m3.group(0))
    return None, None


def extract_venue(text: str) -> Optional[str]:
    m = re.search(r"(?:会议|举办|报到|召开)?(?:地点|地址)\s*[：:]\s*([^\s，。；；]{2,100})", text)
    return m.group(1).strip(" ，。；、") if m else None


def extract_organizer(text: str, default: Optional[str] = None) -> Optional[str]:
    m = re.search(r"主办单位\s*[：:]\s*([^\s，。；；]{2,60})", text)
    return m.group(1).strip(" ，。；、") if m else default


def build_event(source: dict, list_url: str, title: str, detail_url: str,
                start: Optional[str], end: Optional[str], venue: Optional[str],
                organizer: Optional[str], body_text: str = "") -> Event:
    # 优先级：venue → 标题 → 正文（避免正文里的学会地址城市污染）
    province, city = "待确认", "待确认"
    for t in (venue, title, body_text):
        if t:
            p, c = infer_region(t)
            if p != "待确认" or c != "待确认":
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


def _extract_items(html: str, list_url: str, href_re: str) -> dict:
    """从列表页提取 {详情URL: 标题}，同 URL 保留最长标题。

    链接文字为「查看详情/更多」等通用词时，回退读取 <a title="..."> 属性。
    """
    items = {}
    for m in re.finditer(r"<a\s+([^>]*?)>(.*?)</a>", html, re.S | re.I):
        tag, inner = m.group(1), m.group(2)
        hm = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
        if not hm:
            continue
        href = hm.group(1)
        if not re.search(href_re, href):
            continue
        title = re.sub(r"<[^>]+>", " ", inner)
        title = re.sub(r"\s+", " ", title).strip()
        if len(title) < 2 or title in ("查看详情", "更多", "详情", "阅读全文"):
            tm = re.search(r'title=["\']([^"\']+)["\']', tag, re.I)
            if tm:
                title = tm.group(1).strip()
        if not title:
            continue
        full = urljoin(list_url, href)
        if full not in items or len(title) > len(items[full]):
            items[full] = title
    return items


def _scrape_generic_detail(source: dict, client, list_url: str, href_re: str, default_org: str) -> List[Event]:
    res = client.get(list_url)
    if not res:
        return []
    items = _extract_items(res.html, list_url, href_re)
    events: List[Event] = []
    for detail_url, title in items.items():
        if not CONFERENCE_KW.search(title):
            continue
        detail = client.get(detail_url)
        text = strip_html(detail.html) if detail else ""
        start, end = extract_date(text)
        if not start:
            continue
        venue = extract_venue(text)
        organizer = extract_organizer(text, default_org)
        events.append(build_event(source, list_url, title, detail_url, start, end, venue, organizer, body_text=text))
        if len(events) >= 12:
            break
    return events


# ── 中国植物学会（通知公告栏目）────────────────────────────
def scrape_botany(source: dict, client) -> List[Event]:
    return _scrape_generic_detail(source, client, source["list_url"], r"t\d{8}_\d+\.html", "中国植物学会")


# ── 中国遗传学会（学术会议栏目）────────────────────────────
def scrape_gsc(source: dict, client) -> List[Event]:
    return _scrape_generic_detail(source, client, source["list_url"], r"a\d+\.html", "中国遗传学会")


def _clean_cell(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&nbsp;", " ").replace("&ndash;", "-").replace("&mdash;", "—")
           .replace("&ldquo;", "\u201c").replace("&rdquo;", "\u201d")
           .replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<"))
    return re.sub(r"\s+", " ", s).strip()


def parse_plan_date(text: str) -> tuple:
    """解析活动计划里的日期：支持完整范围/单日/仅年月（取当月首末日）。"""
    text = (text or "").strip()
    if not text:
        return None, None
    s, e = parse_date_range(text)
    if s:
        return s, e
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", text)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            last = calendar.monthrange(y, mo)[1]
            return f"{y}-{mo:02d}-01", f"{y}-{mo:02d}-{last:02d}"
    return None, None


def scrape_gsc_plan(source: dict, client) -> List[Event]:
    """中国遗传学会「活动计划」表格：序号|活动名称|参与方式|举办地点|规模|时间|分支机构。"""
    list_url = source["list_url"]
    res = client.get(list_url)
    if not res:
        return []
    events: List[Event] = []
    for tb in re.findall(r"<table[^>]*>(.*?)</table>", res.html, re.S | re.I):
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S | re.I):
            cells = [_clean_cell(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]
            if len(cells) < 7 or not cells[0].isdigit():
                continue
            title, venue, date_text, branch = cells[1], cells[3], cells[5], cells[6]
            if not title:
                continue
            start, end = parse_plan_date(date_text)
            if not start:
                continue
            organizer = f"中国遗传学会（{branch}）" if branch else "中国遗传学会"
            events.append(
                build_event(source, list_url, title, list_url, start, end,
                            venue or None, organizer, body_text=venue)
            )
            if len(events) >= 40:
                break
    return events


# ── 中国计算机学会 CCF（WAF + JS 渲染，用 Playwright）──────
def scrape_ccf(source: dict, client) -> List[Event]:
    """CCF：阿里云 WAF + SPA，用 Playwright 渲染列表页与详情页后解析。"""
    try:
        from scrapers.browser import render_html
    except ImportError:
        print("[ccf] 未安装 playwright，跳过（CI 会安装）")
        return []

    list_url = source["list_url"]
    try:
        html = render_html(list_url, wait_ms=6000)
    except Exception as e:
        print(f"[ccf] 渲染失败 {list_url}: {e}")
        return []

    # 从渲染后的 DOM 提取会议相关链接
    items = {}
    for m in re.finditer(r"<a\s+([^>]*?)>(.*?)</a>", html, re.S | re.I):
        tag, inner = m.group(1), m.group(2)
        hm = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
        if not hm:
            continue
        href = hm.group(1)
        if href.startswith(("#", "javascript:", "mailto:")):
            continue
        text = re.sub(r"<[^>]+>", " ", inner)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or not CONFERENCE_KW.search(text):
            continue
        full = urljoin(list_url, href)
        if full not in items or len(text) > len(items[full]):
            items[full] = text

    events: List[Event] = []
    for detail_url, title in list(items.items())[:8]:
        try:
            dhtml = render_html(detail_url, wait_ms=3000)
        except Exception:
            continue
        text = strip_html(dhtml)
        start, end = extract_date(text)
        if not start:
            continue
        venue = extract_venue(text)
        organizer = extract_organizer(text, "中国计算机学会")
        events.append(build_event(source, list_url, title, detail_url, start, end, venue, organizer, body_text=text))
    return events


ADAPTERS = {
    "cpa": scrape_cpa,
    "caai": scrape_caai,
    "botany": scrape_botany,
    "gsc": scrape_gsc,
    "gsc_plan": scrape_gsc_plan,
    "ccf": scrape_ccf,
}
