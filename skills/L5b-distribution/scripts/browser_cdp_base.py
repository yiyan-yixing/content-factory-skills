"""Base class for browser-based publishers using Playwright CDP.

This is the scripts/ version for the L5b-distribution skill package.
Adapted from biz/content/publish/browser_cdp_base.py — same-directory imports.

Provides shared CDP connection/disconnection and auth check logic
for all platform-specific browser publishers (X, Substack, Zhihu, WeChat).

Prerequisites (common to all browser publishers):
  1. Chrome launched with:
     --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
  2. User logged into the target platform in that Chrome instance
  3. Chrome PAC proxy configured (auto-detects system proxy) for GFW bypass

IMPORTANT: Playwright's sync API cannot run inside an asyncio event loop.
All CDP operations are executed in a separate thread to avoid conflicts.
"""

import logging
import threading
from typing import Optional, Tuple, Callable, Any

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from publisher import Publisher, CONTENT_ROOT

logger = logging.getLogger(__name__)

CDP_URL = "http://127.0.0.1:9222"
TYPE_DELAY_MS = 40  # Simulate human typing speed for editors
POST_WAIT_MS = 4000  # Wait after submitting


def _run_in_thread(fn: Callable, *args, **kwargs) -> Any:
    """Run a function in a separate thread to avoid asyncio event loop conflicts.

    Playwright's sync API creates its own event loop, which conflicts with
    any existing asyncio loop. Running in a separate thread avoids this.
    """
    result = None
    exc = None

    def _worker():
        nonlocal result, exc
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            exc = e

    t = threading.Thread(target=_worker)
    t.start()
    t.join(timeout=120)
    if exc:
        raise exc
    return result


class BrowserCDPPublisher(Publisher):
    """Abstract base class for all browser-CDP-based publishers.

    Subclasses must implement:
      - publish()        — platform-specific publishing logic
      - check_auth()     — check if user is logged in on the platform
      - platform_url     — class attribute: the platform's base URL

    Subclasses may override:
      - compose_url      — the URL to start composing (default: platform_url)
    """

    # Subclasses set these
    platform_name: str = "browser-cdp"
    platform_url: str = ""
    compose_url: str = ""

    def __init__(self, cdp_url: str = CDP_URL):
        self._cdp_url = cdp_url
        self._playwright: Optional[sync_playwright] = None
        self._browser: Optional[Browser] = None

    def _connect(self) -> Tuple[object, Browser, Page]:
        """Connect to Chrome via CDP and return (playwright, browser, page).

        Raises:
            ConnectionError: If Chrome CDP is not reachable.
        """
        try:
            import urllib.request
            urllib.request.urlopen(f"{self._cdp_url}/json/version", timeout=3)
        except Exception:
            raise ConnectionError(
                f"Chrome CDP not reachable at {self._cdp_url}. "
                f"Start Chrome with: open -a 'Google Chrome' --args "
                f"--remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile"
            )

        pw = sync_playwright().start()
        browser = pw.chromium.connect_over_cdp(self._cdp_url)
        context = browser.contexts[0] if browser.contexts else None
        if context is None:
            pw.stop()
            raise ConnectionError("No browser context found in Chrome CDP session")

        page = context.pages[0] if context.pages else context.new_page()
        return pw, browser, page

    def _disconnect(self, pw) -> None:
        """Safely disconnect from Chrome CDP."""
        if pw:
            try:
                pw.stop()
            except Exception:
                pass

    def _run_cdp(self, fn: Callable, *args, **kwargs) -> Any:
        """Run a CDP operation in a separate thread to avoid asyncio conflicts."""
        return _run_in_thread(fn, *args, **kwargs)

    def check_auth(self) -> bool:
        """Check if Chrome CDP is accessible and user is logged in."""
        def _check():
            pw, browser, page = None, None, None
            try:
                pw, browser, page = self._connect()
                page.goto(self.platform_url, timeout=15000)
                page.wait_for_timeout(2000)
                logged_in = self.platform_url.rstrip("/") in page.url
                return logged_in
            except Exception as e:
                logger.warning(
                    "[%s] CDP auth check failed: %s",
                    self.platform_name, str(e)[:100]
                )
                return False
            finally:
                self._disconnect(pw)

        return self._run_cdp(_check)

    def ensure_authenticated(self):
        """Ensure Chrome CDP is accessible.

        Raises:
            ConnectionError: If Chrome CDP is not reachable.
        """
        try:
            import urllib.request
            urllib.request.urlopen(f"{self._cdp_url}/json/version", timeout=3)
        except Exception:
            raise ConnectionError(
                f"Chrome CDP not reachable at {self._cdp_url}. "
                f"Start Chrome with: open -a 'Google Chrome' --args "
                f"--remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile"
            )

    def _type_text(self, page: Page, text: str, delay: int = TYPE_DELAY_MS) -> None:
        """Type text into the currently focused element, simulating human speed."""
        page.keyboard.type(text, delay=delay)

    def _wait_after_submit(self, page: Page, wait_ms: int = POST_WAIT_MS) -> None:
        """Wait after submitting a post/publish action."""
        page.wait_for_timeout(wait_ms)

    def publish(self, article_id: str, dry_run: bool = False, draft_only: bool = False) -> dict:
        """Publish content to the platform. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement publish()")
