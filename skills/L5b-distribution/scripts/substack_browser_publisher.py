"""Substack browser-based publisher using Playwright CDP.

This is the scripts/ version for the L5b-distribution skill package.
Adapted from biz/content/publish/substack_browser_publisher.py — same-directory imports.

Publishes articles to Substack by connecting to a running Chrome instance
that already has the user logged in. This bypasses the GFW block since
Chrome uses the system PAC proxy.

Prerequisites:
  1. Chrome launched with: --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
  2. User logged into substack.com in that Chrome instance (via Google account)
  3. Chrome PAC proxy configured (for GFW bypass — substack.com is blocked in China)

Flow:
  1. Connect to Chrome via CDP (127.0.0.1:9222)
  2. Navigate to {publication_url}/publish/post (article editor)
  3. Type title (textarea[placeholder="Title"])
  4. Type subtitle (textarea[placeholder="Add a subtitle…"])
  5. Type body into ProseMirror contenteditable div
  6. Click "Continue" to open publish settings panel
  7. Click "Send to everyone now" to publish
"""

import logging
import time

from browser_cdp_base import BrowserCDPPublisher, TYPE_DELAY_MS, POST_WAIT_MS
from publisher import (
    get_article_content,
    _parse_markdown,
    CONTENT_ROOT,
)

logger = logging.getLogger(__name__)

# Default publication URL — override via constructor or env
DEFAULT_PUBLICATION_URL = "https://1234366449.substack.com"


class SubstackBrowserPublisher(BrowserCDPPublisher):
    """Publisher for Substack using Playwright CDP browser automation.

    Connects to a running Chrome instance that already has the user
    logged in to Substack (typically via Google account). Publishes
    articles by typing into the Substack editor.
    """

    platform_name = "substack-browser"
    platform_url = "https://substack.com"
    compose_url = ""

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222",
                 publication_url: str = DEFAULT_PUBLICATION_URL):
        super().__init__(cdp_url=cdp_url)
        self._publication_url = publication_url

    def check_auth(self) -> bool:
        """Check if Chrome CDP is accessible and user is logged in to Substack."""
        pw, browser, page = None, None, None
        try:
            pw, browser, page = self._connect()
            page.goto(self._publication_url, timeout=20000)
            page.wait_for_timeout(3000)
            on_substack = "substack.com" in page.url
            return on_substack
        except Exception as e:
            logger.warning(
                "[substack-browser] Auth check failed: %s", str(e)[:100]
            )
            return False
        finally:
            self._disconnect(pw)

    def publish(self, article_id: str, dry_run: bool = False, draft_only: bool = False) -> dict:
        """Publish an article to Substack via browser CDP."""
        result = {
            "success": False,
            "platform": self.platform_name,
            "article_id": article_id,
            "details": "",
            "ids": [],
        }

        content = get_article_content(article_id, "substack")
        if content is None:
            result["details"] = f"Blog file not found for article {article_id}"
            logger.error(result["details"])
            return result

        title, subtitle, body = _parse_markdown(content)
        if not title:
            result["details"] = f"Could not extract title from article {article_id}"
            logger.error(result["details"])
            return result

        logger.info("Article %s: title='%s', subtitle='%s'", article_id, title, subtitle)

        mode = "draft" if draft_only else "publish"
        if dry_run:
            word_count = len(body.split())
            logger.info(
                "[DRY RUN] Would %s Substack article:\n"
                "  Title: %s\n  Subtitle: %s\n  Body: %d words",
                mode, title, subtitle, word_count
            )
            result["success"] = True
            result["details"] = (
                f"DRY RUN: Would {mode} Substack article for {article_id}. "
                f"Title: '{title}', Subtitle: '{subtitle}', Body: {word_count} words"
            )
            return result

        try:
            self.ensure_authenticated()
        except ConnectionError as e:
            result["details"] = str(e)
            logger.error(result["details"])
            return result

        post_url = self._run_cdp(self._publish_via_browser, title, subtitle, body, draft_only)
        if post_url:
            result["success"] = True
            result["ids"] = [post_url]
            result["details"] = (
                f"{'Draft saved' if draft_only else 'Published'} article {article_id} to Substack. "
                f"Title: '{title}', URL: {post_url}"
            )
        else:
            result["details"] = f"Failed to {'save draft for' if draft_only else 'publish'} article {article_id} to Substack"

        return result

    def _publish_via_browser(self, title: str, subtitle: str, body: str,
                              draft_only: bool = False) -> str | None:
        """Publish an article to Substack via browser CDP.

        Key findings from testing:
          - Title is a TEXTAREA (not input): textarea[placeholder="Title"]
          - Subtitle is also a TEXTAREA: textarea[placeholder="Add a subtitle…"]
          - Body editor: .ProseMirror contenteditable (first one)
          - The sidebar input[placeholder="Add a title..."] is NOT the article title
          - Publish button text: "Send to everyone now" (NOT "Publish")
          - Continue button may be blocked by overlay — use JS click
        """
        pw, browser, page = None, None, None
        post_url = None

        try:
            pw, browser, page = self._connect()

            # Step 1: Navigate directly to the publish/post editor page
            editor_url = f"{self._publication_url}/publish/post"
            logger.info("Navigating to Substack editor: %s", editor_url)
            page.goto(editor_url, timeout=20000)
            page.wait_for_timeout(5000)

            # Verify we're on the editor page
            title_check = page.locator('textarea[placeholder="Title"]').first
            if not title_check.is_visible(timeout=5000):
                logger.info("Direct editor URL didn't work, trying Create→Article flow...")
                page.goto(self._publication_url, timeout=20000)
                page.wait_for_timeout(3000)

                create_btn = page.locator('button:has-text("Create")').first
                if create_btn.is_visible(timeout=5000):
                    create_btn.click()
                    page.wait_for_timeout(2000)
                    article_link = page.locator('a:has-text("Article")').first
                    if article_link.is_visible(timeout=5000):
                        article_link.click()
                        page.wait_for_timeout(5000)
                    else:
                        logger.error("Article link not found in Create dropdown")
                        return None
                else:
                    logger.error("Create button not found on publication page")
                    return None

            # Step 2: Enter title (TEXTAREA, not input)
            logger.info("Entering title: '%s'", title)
            title_textarea = page.locator('textarea[placeholder="Title"]').first
            if title_textarea.is_visible(timeout=5000):
                title_textarea.click()
                page.wait_for_timeout(300)
                self._type_text(page, title, delay=TYPE_DELAY_MS)
                page.wait_for_timeout(1000)
            else:
                logger.warning("Could not find title textarea field")

            # Step 3: Enter subtitle
            if subtitle:
                logger.info("Entering subtitle: '%s'", subtitle)
                subtitle_textarea = page.locator('textarea[placeholder*="subtitle"], textarea[placeholder*="Subtitle"]').first
                if subtitle_textarea.is_visible(timeout=3000):
                    subtitle_textarea.click()
                    page.wait_for_timeout(300)
                    self._type_text(page, subtitle, delay=TYPE_DELAY_MS)
                    page.wait_for_timeout(1000)
                else:
                    logger.warning("Could not find subtitle textarea")

            # Step 4: Enter body content into .ProseMirror
            logger.info("Entering body content (%d chars)", len(body))
            body_editor = page.locator('.ProseMirror').first
            if body_editor.is_visible(timeout=5000):
                body_editor.click()
                page.wait_for_timeout(500)
                paragraphs = body.split("\n\n")
                for i, para in enumerate(paragraphs):
                    if i > 0:
                        page.keyboard.press("Enter")
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(200)
                    self._type_text(page, para, delay=TYPE_DELAY_MS)
                    page.wait_for_timeout(300)
            else:
                logger.warning("Could not find body editor")

            page.wait_for_timeout(2000)

            # Step 5: Click "Continue" — use JS click to bypass overlay
            logger.info("Clicking 'Continue' to proceed to publish settings...")
            continue_btn = page.locator('button[data-testid="publish-button"], button:has-text("Continue")').first
            if continue_btn.is_visible(timeout=5000):
                continue_btn.evaluate("el => el.click()")
                page.wait_for_timeout(3000)

            # Step 6: Handle publish settings panel
            if draft_only:
                logger.info("Saving as draft...")
                cancel_btn = page.locator('button:has-text("Cancel")').last
                if cancel_btn.is_visible(timeout=3000):
                    cancel_btn.evaluate("el => el.click()")
                    page.wait_for_timeout(2000)
                logger.info("Article saved as draft (Substack auto-saves)")
            else:
                logger.info("Publishing article from settings panel...")
                publish_btn = page.locator(
                    'button:has-text("Send to everyone"), '
                    'button:has-text("Publish")'
                ).last
                if publish_btn.is_visible(timeout=5000):
                    publish_btn.evaluate("el => el.click()")
                    page.wait_for_timeout(3000)

                    # Handle CTA button prompt
                    publish_wo_btn = page.locator('button:has-text("Publish without")').first
                    if publish_wo_btn.is_visible(timeout=10000):
                        logger.info("Handling 'Publish without buttons' prompt...")
                        publish_wo_btn.evaluate("el => el.click()")
                        page.wait_for_timeout(5000)

                    # Wait for publishing to complete
                    for _ in range(15):
                        still_publishing = page.locator('button:has-text("Publishing")').count()
                        if still_publishing == 0:
                            break
                        page.wait_for_timeout(2000)

                    self._wait_after_submit(page)
                else:
                    logger.warning("Publish/Send button not found on settings page")

            # Step 7: Get published URL
            page.wait_for_timeout(3000)
            current_url = page.url
            if "/p/" in current_url:
                post_url = current_url
                logger.info("Post URL: %s", post_url)
            elif "/share-center" in current_url or "/detail/" in current_url:
                post_link = page.locator('a[href*="/p/"]').first
                if post_link.is_visible(timeout=5000):
                    href = post_link.get_attribute("href") or ""
                    post_url = href if href.startswith("http") else f"{self._publication_url}{href}"
                    logger.info("Post URL from share center: %s", post_url)
                else:
                    post_url = current_url

        except Exception as e:
            logger.error("Substack browser publish error: %s", str(e)[:200])
        finally:
            self._disconnect(pw)

        return post_url
