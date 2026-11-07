"""HTTP 抓取公共能力：限速、重试、UA、robots 尊重（标准库实现，无第三方依赖）。"""
from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from typing import Optional

DEFAULT_UA = "EventAggregatorBot/1.0 (+https://github.com/example/event-aggregator)"


@dataclass
class FetchResult:
    url: str
    status: int
    html: str
    final_url: str


class HttpClient:
    """带限速/重试/退避的简单 HTTP 客户端。"""

    def __init__(
        self,
        user_agent: str = DEFAULT_UA,
        rate_limit_ms: int = 1500,
        timeout_s: int = 20,
        max_retries: int = 3,
        backoff_s: int = 5,
    ):
        self.user_agent = user_agent
        self.rate_limit_ms = rate_limit_ms
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = (time.monotonic() - self._last_request_at) * 1000
        if elapsed < self.rate_limit_ms:
            time.sleep((self.rate_limit_ms - elapsed) / 1000)

    def get(self, url: str) -> Optional[FetchResult]:
        """GET 请求，返回 FetchResult；多次失败返回 None。"""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries):
            self._throttle()
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    self._last_request_at = time.monotonic()
                    body = resp.read()
                    charset = resp.headers.get_content_charset() or "utf-8"
                    html = body.decode(charset, errors="replace")
                    return FetchResult(
                        url=url,
                        status=resp.status,
                        html=html,
                        final_url=resp.geturl(),
                    )
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                last_err = exc
                if attempt < self.max_retries - 1:
                    time.sleep(self.backoff_s * (attempt + 1))
        print(f"[http] 抓取失败 {url}: {last_err}")
        return None


def allow_by_robots(url: str, user_agent: str = DEFAULT_UA) -> bool:
    """检查 robots.txt 是否允许抓取（失败时默认放行）。"""
    try:
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True
