"""静态网站抓取引擎：配置驱动（sources.yaml 的 website 分组）。"""
from __future__ import annotations

from typing import List

from pipeline.models import Event
from pipeline.normalize import parse_date_range, split_requirements
from scrapers.common import HttpClient, allow_by_robots


def _load_yaml(path: str) -> dict:
    import yaml  # PyYAML（仅真实抓取需要）

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _css_first(root, selector: str) -> str:
    """用 lxml.cssselect 提取第一个匹配节点的文本/链接。"""
    from lxml import html as lxml_html

    nodes = root.cssselect(selector)
    if not nodes:
        return ""
    node = nodes[0]
    href = node.get("href") or node.get("src")
    return href if href else (node.text_content() or "").strip()


def _scrape_generic_list(source: dict, client: HttpClient) -> List[Event]:
    """按通用列表选择器抓取一个静态站点。"""
    list_url = source.get("list_url") or ""
    selectors = source.get("selectors") or {}
    if not list_url or not selectors.get("item"):
        print(f"[scrape] 跳过 {source.get('name')}（未配置 list_url/selectors）")
        return []

    if not allow_by_robots(list_url):
        print(f"[scrape] robots 禁止抓取 {list_url}，跳过")
        return []

    result = client.get(list_url)
    if not result:
        return []

    from lxml import html as lxml_html

    root = lxml_html.fromstring(result.html)
    events: List[Event] = []
    item_sel = selectors["item"]
    for node in root.cssselect(item_sel):
        title = _css_first(node, selectors.get("title", ""))
        link = _css_first(node, selectors.get("link", ""))
        date_text = _css_first(node, selectors.get("date", ""))
        venue = _css_first(node, selectors.get("venue", ""))

        if not title:
            continue
        start, end = parse_date_range(date_text)
        url = link if link.startswith("http") else _join_url(list_url, link)

        events.append(
            Event(
                id="",
                title=title,
                type="conference",
                domains=source.get("domains", []),
                fields=source.get("fields", []),
                province="",
                city="",
                venue=venue or "待确认",
                start_date=start or "",
                end_date=end or "",
                url=url or list_url,
                source_url=list_url,
                source_name=source.get("name", ""),
                source_type="website",
                status="upcoming",
                registration_requirements=split_requirements(None),
            )
        )
    return events


def _join_url(base: str, link: str) -> str:
    import urllib.parse

    return urllib.parse.urljoin(base, link)


def scrape_all(config_path: str) -> List[Event]:
    """读取 sources.yaml，抓取所有启用的静态网站源。

    流媒体平台源（公众号/小红书/抖音）由 platform.adapters 处理，默认半自动。
    """
    config = _load_yaml(config_path)
    defaults = config.get("defaults", {})
    client = HttpClient(
        user_agent=defaults.get("user_agent"),
        rate_limit_ms=defaults.get("rate_limit_ms", 1500),
        timeout_s=defaults.get("timeout_s", 20),
        max_retries=defaults.get("max_retries", 3),
        backoff_s=defaults.get("backoff_s", 5),
    )

    from scrapers.sites import ADAPTERS

    events: List[Event] = []
    for source in config.get("sources", {}).get("website", []):
        if not source.get("enabled"):
            print(f"[scrape] 未启用 {source.get('name')}，跳过")
            continue
        adapter = source.get("adapter")
        if adapter in ADAPTERS:
            print(f"[scrape] 抓取 {source.get('name')}（adapter={adapter}）")
            events.extend(ADAPTERS[adapter](source, client))
        else:
            events.extend(_scrape_generic_list(source, client))
    return events
