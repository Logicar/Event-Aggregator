"""流媒体平台适配器占位实现。

统一接口：`fetch_candidates(source: dict) -> List[Event]`
返回进入人工复核队列（review.json）的候选活动。真实抓取需：
- 微信公众号：搜狗微信搜索 + 文章抓取（或已授权的公众号接口）
- 小红书：登录 Cookie + 关键词搜索流
- 抖音：平台搜索接口 / Playwright 渲染
"""
from __future__ import annotations

from typing import List

from pipeline.models import Event


def fetch_candidates(source: dict) -> List[Event]:
    """占位实现：返回空列表。接入真实平台后替换为具体逻辑。"""
    adapter = source.get("adapter", "")
    name = source.get("name", "未命名")
    keywords = source.get("keywords", [])
    print(
        f"[platform] {adapter} 源「{name}」关键词 {keywords} 尚未接入，"
        "需登录态/接口核验后启用（半自动流程）。"
    )
    return []


def fetch_wechat_mp(source: dict) -> List[Event]:
    return fetch_candidates(source)


def fetch_xiaohongshu(source: dict) -> List[Event]:
    return fetch_candidates(source)


def fetch_douyin(source: dict) -> List[Event]:
    return fetch_candidates(source)


ADAPTERS = {
    "wechat_search": fetch_wechat_mp,
    "xiaohongshu_search": fetch_xiaohongshu,
    "douyin_search": fetch_douyin,
}
