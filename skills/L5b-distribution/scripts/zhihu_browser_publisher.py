"""Zhihu (知乎) browser-based publisher using Playwright CDP.

This is the scripts/ version for the L5b-distribution skill package.
Adapted from biz/content/publish/zhihu_browser_publisher.py — same-directory imports.

Publishes articles to Zhihu by connecting to a running Chrome instance
that already has the user logged in. Uses direct content typing since
Zhihu's "Import Markdown Document" feature does NOT work via CDP.

Prerequisites:
  1. Chrome launched with: --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
  2. User logged into zhihu.com in that Chrome instance
  3. No GFW issues — zhihu.com is accessible in China

Flow:
  1. Connect to Chrome via CDP (127.0.0.1:9222)
  2. Navigate to zhuanlan.zhihu.com/write
  3. Scroll to top, enter title in textarea (WriteIndex-titleInput)
  4. Click into editor, type body content (Draft.js auto-converts Markdown)
  5. Open "发布设置" → add topic → click "发布"

Key constraints:
  - MD import does NOT work via CDP — use direct typing instead
  - Title is a TEXTAREA (class=WriteIndex-titleInput), NOT an input element
  - Must scroll to top before entering title
  - Publish/Preview buttons are DISABLED until title is entered
  - Must add a topic via "发布设置" before publishing
  - Draft.js editor: must use keyboard.type(), not page.fill()
"""

import logging
from pathlib import Path

from browser_cdp_base import BrowserCDPPublisher, TYPE_DELAY_MS, POST_WAIT_MS
from publisher import (
    get_article_content,
    CONTENT_ROOT,
)

logger = logging.getLogger(__name__)

ZHIHU_WRITER_URL = "https://zhuanlan.zhihu.com/write"
DISTRIBUTION_DIR = CONTENT_ROOT / "distribution" / "zhihu"


class ZhihuBrowserPublisher(BrowserCDPPublisher):
    """Publisher for Zhihu using Playwright CDP browser automation.

    Connects to a running Chrome instance that already has the user
    logged in to Zhihu. Publishes articles by typing content directly
    into the Zhihu editor (since MD import doesn't work via CDP).
    """

    platform_name = "zhihu-browser"
    platform_url = "https://www.zhihu.com"
    compose_url = ZHIHU_WRITER_URL

    def check_auth(self) -> bool:
        """Check if Chrome CDP is accessible and user is logged in to Zhihu."""
        def _check():
            pw, browser, page = None, None, None
            try:
                pw, browser, page = self._connect()
                page.goto("https://www.zhihu.com/creator", timeout=15000)
                page.wait_for_timeout(2000)
                logged_in = "zhihu.com" in page.url and "signin" not in page.url.lower()
                return logged_in
            except Exception as e:
                logger.warning("[zhihu-browser] Auth check failed: %s", str(e)[:100])
                return False
            finally:
                self._disconnect(pw)

        return self._run_cdp(_check)

    def publish(self, article_id: str, dry_run: bool = False, draft_only: bool = False) -> dict:
        """Publish an article to Zhihu via browser CDP."""
        result = {
            "success": False,
            "platform": self.platform_name,
            "article_id": article_id,
            "details": "",
            "ids": [],
        }

        content = get_article_content(article_id, "zhihu")
        if content is None:
            content_file = DISTRIBUTION_DIR / f"{article_id}-zhihu.md"
            if content_file.exists():
                content = content_file.read_text(encoding="utf-8")
                logger.info("Found Zhihu content file: %s", content_file)
            else:
                result["details"] = f"Zhihu content file not found for article {article_id}"
                logger.error(result["details"])
                return result

        word_count = len(content.split())
        title, body = self._split_title_body(content)

        if dry_run:
            logger.info(
                "[DRY RUN] Would publish Zhihu article for %s. "
                "Title: '%s', Body: %d chars",
                article_id, title, len(body)
            )
            result["success"] = True
            result["details"] = (
                f"DRY RUN: Would {'save draft for' if draft_only else 'publish'} "
                f"Zhihu article for {article_id}. "
                f"Title: '{title}', Body: {len(body)} chars"
            )
            return result

        try:
            self.ensure_authenticated()
        except ConnectionError as e:
            result["details"] = str(e)
            logger.error(result["details"])
            return result

        post_url = self._run_cdp(self._publish_via_browser, title, body, draft_only)
        if post_url:
            result["success"] = True
            result["ids"] = [post_url]
            result["details"] = (
                f"{'Draft saved' if draft_only else 'Published'} article {article_id} to Zhihu. "
                f"Title: '{title}', URL: {post_url}"
            )
        else:
            result["details"] = f"Failed to {'save draft for' if draft_only else 'publish'} article {article_id} to Zhihu"

        return result

    def _publish_via_browser(self, title: str, body: str,
                              draft_only: bool = False) -> str | None:
        """Publish an article to Zhihu via browser CDP using direct typing.

        Key findings from testing:
          - Title is a textarea (class=WriteIndex-titleInput), NOT an input
          - Title field is at top of page, must scroll to top first
          - Publish/Preview buttons are DISABLED until title is entered
          - Must add a topic via "发布设置" panel before publishing
          - Draft.js auto-converts Markdown syntax when typed line-by-line
        """
        pw, browser, page = None, None, None
        post_url = None

        try:
            pw, browser, page = self._connect()

            # Step 1: Navigate to Zhihu article editor
            logger.info("Navigating to Zhihu writer: %s", ZHIHU_WRITER_URL)
            page.goto(ZHIHU_WRITER_URL, timeout=20000)
            page.wait_for_timeout(4000)

            # Step 2: Enter title — CRITICAL: textarea, not input; scroll to top first
            logger.info("Scrolling to top and entering title: '%s'", title)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)

            title_textarea = page.locator(
                'textarea.WriteIndex-titleInput, textarea.Input'
            ).first
            if title_textarea.is_visible(timeout=5000):
                title_textarea.click()
                page.wait_for_timeout(300)
                title_textarea.fill("")
                page.wait_for_timeout(200)
                self._type_text(page, title, delay=TYPE_DELAY_MS)
                page.wait_for_timeout(1000)
                logger.info("Title entered successfully")
            else:
                logger.warning("Could not find title textarea")

            # Step 3: Click into body editor and type content
            logger.info("Clicking into Zhihu body editor...")
            editor = page.locator('[contenteditable="true"]').first
            if editor.is_visible(timeout=5000):
                editor.click()
                page.wait_for_timeout(500)
                page.keyboard.press("Meta+A")
                page.wait_for_timeout(300)
                page.keyboard.press("Backspace")
                page.wait_for_timeout(500)

                logger.info("Typing body content (%d chars)...", len(body))
                lines = body.split("\n")
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(100)
                        continue

                    self._type_text(page, stripped, delay=TYPE_DELAY_MS)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(100)

                page.wait_for_timeout(2000)
            else:
                logger.error("Could not find Zhihu body editor")
                return None

            # Step 4: Verify content
            editor_check = page.locator('[contenteditable="true"]').first
            if editor_check.is_visible(timeout=2000):
                text = editor_check.inner_text()
                if len(text) < 20:
                    logger.warning("Editor content seems empty (only %d chars)", len(text))
                else:
                    logger.info("Content entered successfully (%d chars visible)", len(text))

            # Step 5: Publish or save draft
            if draft_only:
                logger.info("Saving as draft on Zhihu...")
                draft_btn = page.locator('button[aria-label="草稿备份"]').first
                if draft_btn.is_visible(timeout=5000):
                    draft_btn.click()
                    self._wait_after_submit(page, 2000)
                else:
                    logger.info("Zhihu auto-saves drafts — content should be saved")
            else:
                # Add topic (required for publishing)
                logger.info("Opening 发布设置 to add topic...")
                settings_btn = page.locator('button:has-text("发布设置")').first
                if settings_btn.is_visible(timeout=5000):
                    settings_btn.click()
                    page.wait_for_timeout(2000)

                    add_topic = page.locator('button:has-text("添加话题")').first
                    if add_topic.is_visible(timeout=3000):
                        add_topic.click()
                        page.wait_for_timeout(1000)

                        topic_input = page.locator('input[placeholder*="话题"]').first
                        if topic_input.is_visible(timeout=3000):
                            topic_input.click()
                            page.keyboard.type("人工智能", delay=TYPE_DELAY_MS)
                            page.wait_for_timeout(3000)

                            suggestion = page.locator('.Popover-content button').first
                            if suggestion.is_visible(timeout=5000):
                                topic_name = suggestion.inner_text()
                                logger.info("Selecting topic: '%s'", topic_name)
                                suggestion.evaluate("el => el.click()")
                                page.wait_for_timeout(2000)
                            else:
                                logger.warning("Topic suggestion not found")
                        else:
                            logger.warning("Topic input not found")

                # Click publish
                logger.info("Publishing article on Zhihu...")
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(1000)

                publish_btn = page.locator('button:has-text("发布")').last
                if publish_btn.is_visible(timeout=5000):
                    if publish_btn.is_disabled():
                        logger.warning("Publish button is disabled — title or topic missing")
                        editor = page.locator('[contenteditable="true"]').first
                        editor.click()
                        page.wait_for_timeout(500)
                        publish_btn = page.locator('button:has-text("发布")').last
                        if publish_btn.is_disabled():
                            logger.error("Publish button still disabled after retry")
                            return None

                    publish_btn.evaluate("el => el.click()")
                    page.wait_for_timeout(5000)
                    self._wait_after_submit(page)
                else:
                    logger.warning("Publish button not found")

            # Step 6: Get published URL
            page.wait_for_timeout(3000)
            current_url = page.url
            if "/p/" in current_url:
                post_url = current_url.replace("/edit", "")
                logger.info("Post URL: %s", post_url)
            elif "zhuanlan" in current_url:
                post_url = current_url
                logger.info("Post URL: %s", post_url)

        except Exception as e:
            logger.error("Zhihu browser publish error: %s", str(e)[:200])
        finally:
            self._disconnect(pw)

        return post_url

    @staticmethod
    def _split_title_body(content: str) -> tuple[str, str]:
        """Split Markdown content into title and body."""
        lines = content.strip().split("\n")
        start = 0
        if lines and lines[0].strip() == "---":
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    start = i + 1
                    break

        title = ""
        body_start = start
        for i in range(start, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                title = stripped[2:].strip()
                body_start = i + 1
                break

        body = "\n".join(lines[body_start:]).strip()
        return title, body
