#!/usr/bin/env python3
"""run_publish.py — 统一发行 CLI 入口 (L5b-distribution)

从技能包 scripts/ 目录直接运行，无需安装到 Python 包。

用法:
  python3 scripts/run_publish.py --article T1-003 --platform x-browser
  python3 scripts/run_publish.py --article T1-003 --platform all --dry-run
  python3 scripts/run_publish.py --article T1-003 --platform zhihu-browser --draft-only
  python3 scripts/run_publish.py --file /path/to/article.md --platform substack-browser
  python3 scripts/run_publish.py --article T0-TEST --platform substack-browser --verbose

环境变量:
  CONTENT_ROOT  — 内容根目录（默认自动检测 biz/content/）

前置条件:
  Chrome 启动时带: --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile
  用户已登录目标平台

依赖:
  pip install -r scripts/requirements.txt
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# ── 注入 scripts/ 目录到 sys.path ──
# 使同目录的 publisher.py, browser_cdp_base.py 等可直接 import
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from publisher import get_article_content, parse_x_thread, CONTENT_ROOT, _parse_markdown
from x_browser_publisher import XBrowserPublisher
from substack_browser_publisher import SubstackBrowserPublisher
from zhihu_browser_publisher import ZhihuBrowserPublisher
from wechat_browser_publisher import WechatBrowserPublisher

logger = logging.getLogger("L5b-distribution")

# Configure logging
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(verbose: bool = False):
    """Configure logging for the publish module."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT, level=level)


# Platform publisher registry — browser-based only
PLATFORM_PUBLISHERS = {
    "x-browser": XBrowserPublisher,
    "substack-browser": SubstackBrowserPublisher,
    "zhihu-browser": ZhihuBrowserPublisher,
    "wechat-browser": WechatBrowserPublisher,
}

# Default platform set for "all"
ALL_PLATFORMS_DEFAULT = [
    "x-browser",
    "substack-browser",
    "zhihu-browser",
    "wechat-browser",
]


def run_publish(args: argparse.Namespace) -> int:
    """Execute the publish command based on parsed CLI arguments.

    Returns:
        Exit code: 0 for success, 1 for failure, 2 for partial success.
    """
    article_id = args.article
    platform = args.platform
    dry_run = args.dry_run
    draft_only = args.draft_only
    file_path = args.file
    verbose = args.verbose

    setup_logging(verbose)

    logger.info("CONTENT_ROOT: %s", CONTENT_ROOT)

    # Determine which platforms to publish to
    if platform == "all":
        platforms = ALL_PLATFORMS_DEFAULT
    elif platform in PLATFORM_PUBLISHERS:
        platforms = [platform]
    else:
        logger.error(
            "Unknown platform: %s. Supported: %s, all",
            platform, ", ".join(PLATFORM_PUBLISHERS.keys())
        )
        return 1

    logger.info(
        "Publishing article %s to %s (dry_run=%s, draft_only=%s)",
        article_id or f"file:{file_path}", ", ".join(platforms), dry_run, draft_only
    )

    results = []
    exit_code = 0

    for plat in platforms:
        publisher_cls = PLATFORM_PUBLISHERS[plat]
        publisher = publisher_cls()

        # X has no draft mode, so draft_only on X is treated as dry_run
        plat_effective_dry_run = dry_run
        if draft_only and plat == "x-browser" and not dry_run:
            plat_effective_dry_run = True
            logger.info("Note: --draft-only on X.com is treated as --dry-run (X has no draft mode)")

        # Check authentication (skip when dry_run)
        if not plat_effective_dry_run and not publisher.check_auth():
            logger.error(
                "Authentication failed for %s. "
                "Ensure Chrome is running with CDP (--remote-debugging-port=9222) "
                "and you are logged into the target platform.",
                plat
            )
            if len(platforms) == 1:
                return 1
            results.append({
                "platform": plat,
                "success": False,
                "details": "Authentication failed",
            })
            exit_code = max(exit_code, 2)
            continue

        # Handle --file mode: override content loading
        if file_path:
            result = _publish_from_file(publisher, plat, file_path, dry_run, draft_only)
        else:
            result = publisher.publish(article_id, dry_run=dry_run, draft_only=draft_only)

        logger.info(
            "[%s] %s: %s",
            plat.upper(), "OK" if result["success"] else "FAIL", result["details"]
        )
        results.append(result)

        if not result["success"]:
            exit_code = max(exit_code, 2)

    # Summary
    logger.info("=" * 60)
    logger.info("PUBLISH SUMMARY")
    logger.info("=" * 60)
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        ids_str = f" (IDs: {r['ids']})" if r.get("ids") else ""
        logger.info("  [%s] %s: %s%s", r["platform"].upper(), status, r["details"], ids_str)

    total = len(results)
    success_count = sum(1 for r in results if r["success"])
    logger.info("Result: %d/%d platforms succeeded", success_count, total)

    return exit_code


def _publish_from_file(
    publisher, platform: str, file_path: str, dry_run: bool, draft_only: bool
) -> dict:
    """Publish content from a directly specified file path."""
    path = Path(file_path)
    if not path.exists():
        return {
            "success": False,
            "platform": platform,
            "article_id": f"file:{file_path}",
            "details": f"File not found: {file_path}",
            "ids": [],
        }

    content = path.read_text(encoding="utf-8")

    if platform == "x-browser":
        effective_dry_run = dry_run or draft_only
        if draft_only and not dry_run:
            logger.info("--draft-only on X.com is treated as --dry-run (X has no draft mode)")

        tweets = parse_x_thread(content)
        if not tweets:
            return {
                "success": False,
                "platform": platform,
                "article_id": f"file:{file_path}",
                "details": "No tweets parsed from file",
                "ids": [],
            }
        if effective_dry_run:
            for i, tweet in enumerate(tweets, 1):
                logger.info(
                    "[DRY RUN] Tweet %d/%d (%d chars):\n%s",
                    i, len(tweets), len(tweet), tweet
                )
            return {
                "success": True,
                "platform": platform,
                "article_id": f"file:{file_path}",
                "details": f"DRY RUN: Would post {len(tweets)} tweets",
                "ids": [],
            }
        try:
            publisher.ensure_authenticated()
        except ConnectionError as e:
            return {
                "success": False,
                "platform": platform,
                "article_id": f"file:{file_path}",
                "details": f"CDP auth failed: {e}",
                "ids": [],
            }
        tweet_ids = publisher._post_thread_via_browser(tweets)
        return {
            "success": bool(tweet_ids),
            "platform": platform,
            "article_id": f"file:{file_path}",
            "details": f"Posted {len(tweet_ids)} tweets" if tweet_ids else "Failed to post thread",
            "ids": tweet_ids,
        }

    if platform == "substack-browser":
        title, subtitle, body = _parse_markdown(content)
        if not title:
            return {
                "success": False,
                "platform": platform,
                "article_id": f"file:{file_path}",
                "details": "Could not extract title from file",
                "ids": [],
            }
        if dry_run:
            mode = "draft" if draft_only else "publish"
            logger.info(
                "[DRY RUN] Substack %s: title='%s', subtitle='%s', %d words",
                mode, title, subtitle, len(body.split())
            )
            return {
                "success": True,
                "platform": platform,
                "article_id": f"file:{file_path}",
                "details": f"DRY RUN: Would {mode} draft '{title}'",
                "ids": [],
            }
        try:
            publisher.ensure_authenticated()
        except ConnectionError as e:
            return {
                "success": False,
                "platform": platform,
                "article_id": f"file:{file_path}",
                "details": f"CDP auth failed: {e}",
                "ids": [],
            }
        post_url = publisher._run_cdp(
            publisher._publish_via_browser, title, subtitle, body, draft_only
        )
        return {
            "success": bool(post_url),
            "platform": platform,
            "article_id": f"file:{file_path}",
            "details": (
                f"{'Draft saved' if draft_only else 'Published'}: title='{title}', URL={post_url}"
                if post_url else f"Failed to {'save draft' if draft_only else 'publish'}"
            ),
            "ids": [post_url] if post_url else [],
        }

    # For zhihu-browser and wechat-browser, delegate to publish
    return publisher.publish(
        f"file:{file_path}", dry_run=dry_run, draft_only=draft_only
    )


def main():
    """Parse CLI arguments and run the publish command."""
    parser = argparse.ArgumentParser(
        description="L5b-distribution: Browser CDP content publisher for 4 channels",
        prog="python3 scripts/run_publish.py",
    )

    # Article selection (mutually exclusive group)
    article_group = parser.add_mutually_exclusive_group(required=True)
    article_group.add_argument(
        "--article", "-a",
        help="Article ID to publish (e.g. T1-003)"
    )
    article_group.add_argument(
        "--file", "-f",
        help="Direct path to content file (bypasses article registry)"
    )

    # Platform selection
    parser.add_argument(
        "--platform", "-p",
        required=True,
        choices=[
            "x-browser",
            "substack-browser",
            "zhihu-browser",
            "wechat-browser",
            "all",
        ],
        help=(
            "Target platform. 'all' publishes to all 4 channels. "
            "Browser CDP mode bypasses GFW and API limitations."
        )
    )

    # Mode flags
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Preview what would be published without making any changes"
    )
    parser.add_argument(
        "--draft-only",
        action="store_true",
        help=(
            "Create draft only. Substack: don't publish; X: same as dry-run; "
            "WeChat: default terminal state (human publishes via phone)"
        )
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()
    sys.exit(run_publish(args))


if __name__ == "__main__":
    main()
