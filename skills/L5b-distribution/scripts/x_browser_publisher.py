"""X.com (Twitter) browser-based publisher using Playwright CDP.

This is the scripts/ version for the L5b-distribution skill package.
Adapted from biz/content/publish/x_browser_publisher.py — same-directory imports.

Posts tweet threads by connecting to a running Chrome instance via CDP.
No API key required — uses the browser's login session directly.

Prerequisites:
  1. Chrome launched with: --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
  2. User logged into x.com in that Chrome instance
  3. Chrome PAC proxy configured (auto-detects system proxy) for GFW bypass
"""

import logging
import os
import time

from browser_cdp_base import BrowserCDPPublisher, TYPE_DELAY_MS, POST_WAIT_MS
from publisher import (
    get_article_content,
    parse_x_thread,
    CONTENT_ROOT,
)

logger = logging.getLogger(__name__)

# Configurable URLs — override via environment variables
X_BASE_URL = os.environ.get("X_BASE_URL", "https://x.com")
X_PROFILE_HANDLE = os.environ.get("X_PROFILE_HANDLE", "1yan1xing")
COMPOSE_URL = f"{X_BASE_URL}/compose/post"
# Derived hostname for auth-check string matching (e.g. "x.com" or "twitter.com")
_X_HOST = X_BASE_URL.replace("https://", "").replace("http://", "").rstrip("/")


class XBrowserPublisher(BrowserCDPPublisher):
    """Publisher for X.com using Playwright CDP browser automation.

    Connects to a running Chrome instance that already has the user
    logged in. Posts tweet threads by typing into the compose box
    and using keyboard shortcuts to submit.
    """

    platform_name = "x-browser"
    platform_url = f"{X_BASE_URL}/home"
    compose_url = COMPOSE_URL

    def check_auth(self) -> bool:
        """Check if Chrome CDP is accessible and user is logged in to X.com."""
        def _check():
            pw, browser, page = None, None, None
            try:
                pw, browser, page = self._connect()
                page.goto(f"{X_BASE_URL}/home", timeout=15000)
                page.wait_for_timeout(2000)
                logged_in = f"{_X_HOST}/home" in page.url or _X_HOST in page.url
                return logged_in
            except Exception as e:
                logger.warning("CDP auth check failed: %s", str(e)[:100])
                return False
            finally:
                self._disconnect(pw)

        return self._run_cdp(_check)

    def publish(self, article_id: str, dry_run: bool = False, draft_only: bool = False) -> dict:
        """Publish a tweet thread for the given article.

        Args:
            article_id: Article identifier (e.g. "T1-003").
            dry_run: If True, preview without posting.
            draft_only: Treated as dry_run (X has no draft mode).

        Returns:
            Result dict with success, platform, article_id, details, ids.
        """
        result = {
            "success": False,
            "platform": self.platform_name,
            "article_id": article_id,
            "details": "",
            "ids": [],
        }

        content = get_article_content(article_id, "x")
        if content is None:
            result["details"] = f"X thread file not found for article {article_id}"
            logger.error(result["details"])
            return result

        tweets = parse_x_thread(content)
        if not tweets:
            result["details"] = f"No tweets parsed for article {article_id}"
            logger.error(result["details"])
            return result

        if dry_run or draft_only:
            mode = "draft (dry-run)" if draft_only else "dry-run"
            counts = [len(t) for t in tweets]
            logger.info(
                "[%s] Would post %d tweets as thread for %s. Chars: %s",
                mode.upper(), len(tweets), article_id, counts
            )
            result["success"] = True
            result["details"] = (
                f"DRY RUN: Would post {len(tweets)} tweets as a thread for {article_id}. "
                f"Character counts: {counts}"
            )
            return result

        try:
            self.ensure_authenticated()
        except ConnectionError as e:
            result["details"] = str(e)
            logger.error(result["details"])
            return result

        tweet_ids = self._run_cdp(self._post_thread_via_browser, tweets)
        if tweet_ids:
            result["success"] = True
            result["ids"] = tweet_ids
            result["details"] = (
                f"Posted {len(tweet_ids)}/{len(tweets)} tweets as a thread for {article_id}."
            )
        else:
            result["details"] = f"Failed to post thread for {article_id}"

        return result

    def _post_thread_via_browser(self, tweets: list[str]) -> list[str]:
        """Post a thread of tweets via browser CDP.

        Strategy:
          1. Post first tweet via compose page
          2. For subsequent tweets: navigate to reply URL and type + post
        """
        pw, browser, page = None, None, None
        posted_urls = []

        try:
            pw, browser, page = self._connect()

            # Post first tweet
            logger.info("Posting tweet 1/%d via compose page", len(tweets))
            page.goto(COMPOSE_URL, timeout=20000)
            page.wait_for_timeout(2000)

            editor = page.get_by_role("textbox", name="Post text").first
            editor.click()
            page.wait_for_timeout(500)

            page.keyboard.type(tweets[0], delay=TYPE_DELAY_MS)
            page.wait_for_timeout(1500)

            # Post via keyboard shortcut
            page.keyboard.press("Meta+Enter")
            self._wait_after_submit(page)

            # Get posted tweet URL from profile
            profile_url = f"{X_BASE_URL}/{X_PROFILE_HANDLE}"
            page.goto(profile_url, timeout=15000)
            page.wait_for_timeout(3000)

            first_tweet_el = page.locator('[data-testid="tweetText"]').first
            if first_tweet_el.is_visible(timeout=5000):
                tweet_link = page.locator('article [data-testid="tweetText"] >> xpath=ancestor::article').first.locator('a[href*="/status/"]').first
                if tweet_link.is_visible(timeout=3000):
                    href = tweet_link.get_attribute("href")
                    if href:
                        posted_urls.append(f"{X_BASE_URL}{href}" if href.startswith("/") else href)
                        logger.info("Tweet 1 posted: %s", posted_urls[-1])

            # Post remaining tweets as replies
            for i, tweet_text in enumerate(tweets[1:], 2):
                logger.info("Posting tweet %d/%d as reply", i, len(tweets))
                time.sleep(2)  # Rate limit courtesy

                if posted_urls:
                    last_url = posted_urls[-1]
                    page.goto(last_url, timeout=15000)
                    page.wait_for_timeout(2000)

                    reply_btn = page.locator('[data-testid="reply"]').first
                    if reply_btn.is_visible(timeout=3000):
                        reply_btn.click()
                        page.wait_for_timeout(2000)

                        reply_editor = page.get_by_role("textbox", name="Post text").first
                        reply_editor.click()
                        page.wait_for_timeout(500)
                        page.keyboard.type(tweet_text, delay=TYPE_DELAY_MS)
                        page.wait_for_timeout(1500)

                        page.keyboard.press("Meta+Enter")
                        self._wait_after_submit(page)

                        logger.info("Tweet %d/%d posted as reply", i, len(tweets))
                    else:
                        logger.warning("Reply button not found for tweet %d", i - 1)
                        break
                else:
                    logger.warning("Cannot post reply - no previous tweet URL")
                    break

        except Exception as e:
            logger.error("Browser publish error: %s", str(e)[:200])
        finally:
            self._disconnect(pw)

        return posted_urls
