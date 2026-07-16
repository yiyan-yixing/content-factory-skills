"""WeChat Official Account (微信公众号) browser-based publisher using Playwright CDP.

This is the scripts/ version for the L5b-distribution skill package.
Adapted from biz/content/publish/wechat_browser_publisher.py — same-directory imports.

Publishes articles to WeChat by connecting to a running Chrome instance
that already has the user logged in. Due to WeChat's 2025 API changes,
personal subscription accounts can only create drafts — publishing
requires human phone confirmation.

Prerequisites:
  1. Chrome launched with: --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
  2. User logged into mp.weixin.qq.com in that Chrome instance (QR code scan)
  3. No GFW issues — mp.weixin.qq.com is accessible in China

Flow:
  1. Connect to Chrome via CDP (127.0.0.1:9222)
  2. Navigate to 草稿箱 (draft box) page with valid token
  3. Click "新的创作" button → "文章" dropdown option
  4. Editor opens in a NEW TAB — switch to it
  5. Dismiss any dialog (e.g. "开通" / "稍后再说")
  6. Enter title in first .ProseMirror contenteditable
  7. Enter body in second .ProseMirror contenteditable
  8. Click "保存为草稿" (Save as draft) — automation stops here
  9. Human confirms publish on phone

Key constraints:
  - API publishing NOT available for personal subscription accounts (revoked 2025.7)
  - Playwright automation can only save as draft
  - Publishing requires human phone confirmation (cannot be automated)
  - Editor opens in a NEW BROWSER TAB — must switch to the new page
  - Must dismiss any overlay dialogs before interacting with editor
  - Editor uses ProseMirror — use keyboard.type() with delay
  - Title is the first .ProseMirror (data-placeholder="请在这里输入标题")
  - Body is the second .ProseMirror (has larger height box)
  - Must extract token from existing WeChat admin page URL
"""

import logging
from pathlib import Path

from browser_cdp_base import BrowserCDPPublisher, TYPE_DELAY_MS, POST_WAIT_MS
from publisher import (
    get_article_content,
    CONTENT_ROOT,
)

logger = logging.getLogger(__name__)

WECHAT_ADMIN_URL = "https://mp.weixin.qq.com"
DISTRIBUTION_DIR = CONTENT_ROOT / "distribution" / "wechat"


def _redact_token(url: str) -> str:
    """Redact token parameter from a URL for safe logging."""
    import re
    return re.sub(r'token=\d+', 'token=****', url)


class WechatBrowserPublisher(BrowserCDPPublisher):
    """Publisher for WeChat Official Account using Playwright CDP.

    Connects to a running Chrome instance that already has the user
    logged in to WeChat admin. Creates article drafts by typing
    into ProseMirror editors.

    Note: Publishing requires human phone confirmation — automation
    can only save drafts. This is a WeChat platform limitation.
    """

    platform_name = "wechat-browser"
    platform_url = WECHAT_ADMIN_URL
    compose_url = WECHAT_ADMIN_URL

    def check_auth(self) -> bool:
        """Check if Chrome CDP is accessible and user is logged in to WeChat admin."""
        pw, browser, page = None, None, None
        try:
            pw, browser, page = self._connect()
            page.goto(WECHAT_ADMIN_URL, timeout=15000)
            page.wait_for_timeout(3000)
            on_admin = "mp.weixin.qq.com" in page.url and "login" not in page.url.lower()
            return on_admin
        except Exception as e:
            logger.warning("[wechat-browser] Auth check failed: %s", str(e)[:100])
            return False
        finally:
            self._disconnect(pw)

    def publish(self, article_id: str, dry_run: bool = False, draft_only: bool = False) -> dict:
        """Publish an article to WeChat Official Account via browser CDP.

        Since WeChat requires human phone confirmation for publishing,
        this always saves as draft.
        """
        result = {
            "success": False,
            "platform": self.platform_name,
            "article_id": article_id,
            "details": "",
            "ids": [],
        }

        content = get_article_content(article_id, "wechat")
        if content is None:
            content_file = DISTRIBUTION_DIR / f"{article_id}-wechat.md"
            if content_file.exists():
                content = content_file.read_text(encoding="utf-8")
                logger.info("Found WeChat content file: %s", content_file)
            else:
                result["details"] = f"WeChat content file not found for article {article_id}"
                logger.error(result["details"])
                return result

        word_count = len(content.split())
        title = self._extract_title(content)

        if dry_run:
            logger.info(
                "[DRY RUN] Would create WeChat draft for %s. "
                "Title: '%s', Content: %d words",
                article_id, title, word_count
            )
            result["success"] = True
            result["details"] = (
                f"DRY RUN: Would create WeChat draft for {article_id}. "
                f"Title: '{title}', Content: {word_count} words. "
                f"Note: Publishing requires human phone confirmation."
            )
            return result

        try:
            self.ensure_authenticated()
        except ConnectionError as e:
            result["details"] = str(e)
            logger.error(result["details"])
            return result

        draft_id = self._run_cdp(self._create_draft_via_browser, article_id, content)
        if draft_id:
            result["success"] = True
            result["ids"] = [draft_id]
            result["details"] = (
                f"Draft saved for article {article_id} on WeChat. "
                f"Title: '{title}'. "
                f"Publishing requires human phone confirmation — "
                f"open WeChat admin to confirm."
            )
        else:
            result["details"] = f"Failed to create draft for article {article_id} on WeChat"

        return result

    def _create_draft_via_browser(self, article_id: str, content: str) -> str | None:
        """Create a draft article on WeChat via browser CDP.

        Strategy:
          1. Navigate to WeChat admin and extract token
          2. Go to 草稿箱 page with valid token
          3. Click "新的创作" → "文章" to open editor in new tab
          4. Switch to the editor tab
          5. Dismiss any dialog overlays
          6. Enter title in first ProseMirror, body in second ProseMirror
          7. Click "保存为草稿"
        """
        pw, browser, page = None, None, None
        draft_id = None

        try:
            pw, browser, page = self._connect()

            # Step 1: Navigate to WeChat admin to get a valid token
            logger.info("Navigating to WeChat admin to extract token...")
            page.goto(WECHAT_ADMIN_URL, timeout=20000)
            page.wait_for_timeout(3000)

            import re
            current_url = page.url
            token_match = re.search(r'token=(\d+)', current_url)
            if not token_match:
                logger.error("Could not extract token from WeChat URL: %s", _redact_token(current_url))
                return None
            token = token_match.group(1)
            logger.info("Extracted WeChat token: ****%s", token[-4:] if len(token) > 4 else "***")

            # Step 2: Navigate to 草稿箱 (draft box) page
            draft_url = (
                f"https://mp.weixin.qq.com/cgi-bin/appmsg?"
                f"begin=0&count=10&type=77&action=list_card&"
                f"token={token}&lang=zh_CN"
            )
            logger.info("Navigating to 草稿箱: %s", _redact_token(draft_url))
            page.goto(draft_url, timeout=20000)
            page.wait_for_timeout(3000)

            # Step 3: Click "新的创作" button to open dropdown
            logger.info("Clicking '新的创作' button...")
            new_create_btn = page.locator('button:has-text("新的创作")').first
            if new_create_btn.is_visible(timeout=5000):
                new_create_btn.click()
                page.wait_for_timeout(1500)

                # Click "文章" option from dropdown
                article_option = page.locator(
                    '.weui-desktop-dropdown__list-ele:has-text("文章")'
                ).first
                if article_option.is_visible(timeout=3000):
                    article_option.click()
                    page.wait_for_timeout(3000)

                    # Step 4: Switch to the new editor tab
                    context = browser.contexts[0]
                    editor_page = None
                    for pg in context.pages:
                        if 'appmsg_edit' in pg.url:
                            editor_page = pg
                            break

                    if not editor_page:
                        logger.error("Editor page not found after clicking 文章")
                        return None

                    page = editor_page
                    logger.info("Switched to editor page: %s", _redact_token(page.url))
                    page.wait_for_timeout(3000)
                else:
                    logger.error("文章 option not found in dropdown")
                    return None
            else:
                logger.error("'新的创作' button not found on draft page")
                return None

            # Step 5: Dismiss any dialog overlay
            dismiss_btn = page.locator('button:has-text("稍后再说"), button:has-text("取消")').first
            if dismiss_btn.is_visible(timeout=3000):
                dismiss_btn.click()
                page.wait_for_timeout(1000)
                logger.info("Dismissed overlay dialog")

            # Step 6: Enter title in first ProseMirror
            title = self._extract_title(content)
            if title:
                logger.info("Entering title: '%s'", title)
                title_editor = page.locator('.ProseMirror').first
                if title_editor.is_visible(timeout=5000):
                    title_editor.click()
                    page.wait_for_timeout(300)
                    self._type_text(page, title, delay=TYPE_DELAY_MS)
                    page.wait_for_timeout(1000)

            # Step 7: Enter body content in second ProseMirror
            logger.info("Entering body content...")
            body_content = self._strip_title(content)
            body_editor = page.locator('.ProseMirror').last
            if body_editor.is_visible(timeout=5000):
                body_editor.click()
                page.wait_for_timeout(500)
                paragraphs = body_content.split("\n\n")
                for i, para in enumerate(paragraphs):
                    stripped = para.strip()
                    if not stripped:
                        continue
                    if i > 0:
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(200)
                    self._type_text(page, stripped, delay=TYPE_DELAY_MS)
                    page.wait_for_timeout(200)

            page.wait_for_timeout(2000)

            # Step 8: Save as draft
            logger.info("Saving WeChat draft...")
            save_btn = page.locator('button:has-text("保存为草稿")').first
            if save_btn.is_visible(timeout=5000):
                save_btn.click()
                page.wait_for_timeout(3000)
                logger.info("Draft saved successfully")
            else:
                logger.warning("Save draft button not found")

            # Step 9: Get draft info
            page.wait_for_timeout(2000)
            current_url = page.url
            if "appmsg_edit" in current_url:
                id_match = re.search(r'appmsgid=(\d+)', current_url)
                if id_match:
                    draft_id = id_match.group(1)
                else:
                    draft_id = "saved"
                logger.info("Draft saved: %s", draft_id)

        except Exception as e:
            logger.error("WeChat browser publish error: %s", str(e)[:200])
        finally:
            self._disconnect(pw)

        return draft_id

    @staticmethod
    def _extract_title(content: str) -> str:
        """Extract the title from a Markdown file for WeChat."""
        lines = content.strip().split("\n")
        start = 0
        if lines and lines[0].strip() == "---":
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    start = i + 1
                    break

        for i in range(start, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                return stripped[2:].strip()
        return ""

    @staticmethod
    def _strip_title(content: str) -> str:
        """Remove the H1 title line from content (since title is entered separately)."""
        lines = content.strip().split("\n")
        start = 0
        if lines and lines[0].strip() == "---":
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    start = i + 1
                    break

        result_lines = []
        title_removed = False
        for i in range(start, len(lines)):
            stripped = lines[i].strip()
            if not title_removed and stripped.startswith("# ") and not stripped.startswith("## "):
                title_removed = True
                continue
            result_lines.append(lines[i])

        return "\n".join(result_lines).strip()
