"""Playwright 无头浏览器渲染：用于 JS 渲染 + WAF 站点（如 CCF）。

依赖（仅启用此类源时需要）：
    pip install playwright
    python -m playwright install --with-deps chromium
"""
from __future__ import annotations

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def render_html(url: str, wait_ms: int = 4000, timeout_ms: int = 45000) -> str:
    """用 Chromium 渲染页面并返回渲染后的 HTML。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=UA)
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(wait_ms)  # 等待 JS/WAF 挑战完成
        html = page.content()
        browser.close()
        return html
