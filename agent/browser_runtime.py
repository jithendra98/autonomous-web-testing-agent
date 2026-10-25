"""
Browser Runtime & Chrome DevTools Protocol (CDP) Telemetry Manager
Manages Playwright lifecycle, CDP session, network HAR logging, console error interception,
and screenshot artifact capture.
"""

from typing import List, Dict, Any, Optional
import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page, CDPSession


class BrowserRuntime:
    """
    High-performance async browser runtime with deep CDP telemetry.
    """

    def __init__(self, headless: bool = False, slow_mo: int = 400):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cdp_session: Optional[CDPSession] = None

        # Telemetry logs
        self.console_logs: List[Dict[str, Any]] = []
        self.failed_requests: List[Dict[str, Any]] = []
        self.all_network_requests: List[Dict[str, Any]] = []

    async def start(self) -> Page:
        """Launches Chromium browser and initializes CDP hooks."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()

        # Attach Playwright Event Handlers
        self.page.on("console", self._handle_console)
        self.page.on("requestfailed", self._handle_request_failed)
        self.page.on("response", self._handle_response)

        # Attach low-level CDP session
        try:
            self.cdp_session = await self.context.new_cdp_session(self.page)
            await self.cdp_session.send("Performance.enable")
            await self.cdp_session.send("Network.enable")
        except Exception:
            pass

        return self.page

    def _handle_console(self, msg):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }
        self.console_logs.append(log_entry)

    def _handle_request_failed(self, request):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": request.url,
            "method": request.method,
            "failure": request.failure
        }
        self.failed_requests.append(entry)

    def _handle_response(self, response):
        if response.status >= 400:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text
            }
            self.failed_requests.append(entry)

    async def get_cdp_performance_metrics(self) -> Dict[str, Any]:
        """Queries Chrome DevTools Protocol for heap and layout metrics."""
        if not self.cdp_session:
            return {}
        try:
            res = await self.cdp_session.send("Performance.getMetrics")
            metrics = {m["name"]: m["value"] for m in res.get("metrics", [])}
            return {
                "js_heap_used_mb": round(metrics.get("JSHeapUsedSize", 0) / (1024 * 1024), 2),
                "dom_nodes_count": metrics.get("Nodes", 0),
                "js_event_listeners": metrics.get("JSEventListeners", 0),
                "layout_count": metrics.get("LayoutCount", 0)
            }
        except Exception:
            return {}

    async def capture_screenshot(self, filepath: str) -> str:
        """Captures a screenshot artifact."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if self.page:
            await self.page.screenshot(path=filepath, full_page=True)
        return filepath

    async def close(self):
        """Clean shutdown of browser and context."""
        if self.cdp_session:
            try:
                await self.cdp_session.detach()
            except Exception:
                pass
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
