"""Abstract base class for content publishers + content utilities.

This is the scripts/ version for the L5b-distribution skill package.
Adapted from biz/content/publish/publisher.py — same-directory imports
(no relative package imports).

Provides:
  - Publisher ABC
  - get_article_content() — read article content from filesystem
  - parse_x_thread() — parse X thread markdown into tweet list
  - SubstackPublisher._parse_markdown() — extract title/subtitle/body
  - load_env_file() — simple .env parser
"""

import os
import re
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# CONTENT_ROOT: where content files live.
# Priority: CONTENT_ROOT env var > auto-detect from script location.
# When installed in .claude/skills/L5b-distribution/scripts/, we walk up
# to find the biz/content/ directory.
_SCRIPT_DIR = Path(__file__).resolve().parent
_env_root = os.getenv("CONTENT_ROOT", "")
if _env_root:
    CONTENT_ROOT = Path(_env_root)
else:
    # Auto-detect: scripts/ is under .claude/skills/L5b-distribution/
    # Walk up 4 levels: scripts → L5b-distribution → skills → .claude → biz/content
    # The 4th parent IS the content root (biz/content/).
    # Verify by checking for distribution/ directory.
    _walk_up = _SCRIPT_DIR.parent.parent.parent.parent
    if (_walk_up / "distribution").exists():
        CONTENT_ROOT = _walk_up
    else:
        # Fallback: try 3 levels up (workshop/content-factory-skills/skills/L5b-dist/scripts/)
        _walk_up3 = _SCRIPT_DIR.parent.parent.parent
        # From workshop root, look for biz/content
        for ancestor in [_walk_up3, _walk_up3.parent, _walk_up3.parent.parent]:
            candidate = ancestor / "biz" / "content"
            if candidate.exists() and (candidate / "distribution").exists():
                CONTENT_ROOT = candidate
                break
        else:
            # Last resort: use CWD's biz/content/ or CWD itself
            _cwd = Path.cwd()
            if (_cwd / "distribution").exists():
                CONTENT_ROOT = _cwd
            elif (_cwd / "biz" / "content").exists():
                CONTENT_ROOT = _cwd / "biz" / "content"
            else:
                CONTENT_ROOT = _cwd

# Platform-specific content directories
PLATFORM_DIRS = {
    "x": CONTENT_ROOT / "distribution" / "x-threads",
    "substack": CONTENT_ROOT / "blog",
    "zhihu": CONTENT_ROOT / "distribution" / "zhihu",
    "wechat": CONTENT_ROOT / "distribution" / "wechat",
}

# Valid article ID pattern: alphanumeric, hyphens, underscores only.
# Prevents path traversal via article_id containing "../".
ARTICLE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# Known article ID to blog filename mapping (Substack).
# Blog files use date-slug naming, so a direct lookup is needed.
ARTICLE_BLOG_MAP = {
    "T1-001": "2026-07-14-i-gave-claude-11-quantitative-trading-agents.md",
    "T1-002": "2026-07-14-the-ai-operating-system-for-a-one-person-company.md",
    "T1-003": "2026-07-14-your-ai-agents-need-sleep.md",
    "T0-TEST": "2026-07-15-hello-from-yiyan-yixing.md",
}


class Publisher(ABC):
    """Abstract base class for all platform publishers.

    Subclasses must implement the `publish` method, which takes an article_id
    and optional dry_run / draft_only flags.
    """

    @abstractmethod
    def publish(self, article_id: str, dry_run: bool = False, draft_only: bool = False) -> dict:
        """Publish an article to the platform.

        Args:
            article_id: Article identifier (e.g. "T1-003").
            dry_run: If True, log actions without actually publishing.
            draft_only: If True, create a draft without publishing (Substack).

        Returns:
            dict with keys: success, platform, article_id, details, ids.
        """
        ...

    @abstractmethod
    def check_auth(self) -> bool:
        """Check if authentication credentials are available and valid."""
        ...


def _validate_article_id(article_id: str) -> bool:
    """Validate that article_id matches the safe pattern (no path traversal)."""
    if not ARTICLE_ID_RE.match(article_id):
        logger.error(
            "Invalid article_id '%s': must contain only alphanumeric, hyphens, underscores",
            article_id
        )
        return False
    return True


def get_article_content(article_id: str, platform: str) -> Optional[str]:
    """Read article content from the filesystem based on article_id and platform.

    Resolution logic per platform:
        - x: Look for {article_id}-x-thread.md in distribution/x-threads/
        - substack: Look up article_id in ARTICLE_BLOG_MAP, then read from blog/
        - zhihu: Look for {article_id}-zhihu.md (or latest -vN version)
        - wechat: Look for {article_id}-wechat.md (or latest -vN version)
    """
    if not _validate_article_id(article_id):
        return None

    if platform not in PLATFORM_DIRS:
        logger.error("Unknown platform: %s. Supported: %s", platform, list(PLATFORM_DIRS.keys()))
        return None

    content_dir = PLATFORM_DIRS[platform]

    if platform == "x":
        filepath = content_dir / f"{article_id}-x-thread.md"
        if filepath.exists():
            logger.info("Found X thread file: %s", filepath)
            return filepath.read_text(encoding="utf-8")
        logger.error("X thread file not found: %s", filepath)
        return None

    if platform == "substack":
        if article_id in ARTICLE_BLOG_MAP:
            filepath = content_dir / ARTICLE_BLOG_MAP[article_id]
            if filepath.exists():
                logger.info("Found Substack blog file: %s", filepath)
                return filepath.read_text(encoding="utf-8")
            logger.error("Substack blog file not found: %s", filepath)
            return None
        logger.warning("Article ID %s not in blog registry, searching directory...", article_id)
        for f in content_dir.glob("*.md"):
            if article_id.lower() in f.name.lower():
                logger.info("Found candidate blog file: %s", f)
                return f.read_text(encoding="utf-8")
        logger.error("No blog file found for article ID: %s", article_id)
        return None

    if platform == "zhihu":
        candidates = sorted(content_dir.glob(f"{article_id}-zhihu-v*.md"))
        if candidates:
            filepath = candidates[-1]
            logger.info("Found Zhihu content file (latest version): %s", filepath)
            return filepath.read_text(encoding="utf-8")
        filepath = content_dir / f"{article_id}-zhihu.md"
        if filepath.exists():
            logger.info("Found Zhihu content file: %s", filepath)
            return filepath.read_text(encoding="utf-8")
        logger.error("Zhihu content file not found: %s", filepath)
        return None

    if platform == "wechat":
        candidates = sorted(content_dir.glob(f"{article_id}-wechat-v*.md"))
        if candidates:
            filepath = candidates[-1]
            logger.info("Found WeChat content file (latest version): %s", filepath)
            return filepath.read_text(encoding="utf-8")
        filepath = content_dir / f"{article_id}-wechat.md"
        if filepath.exists():
            logger.info("Found WeChat content file: %s", filepath)
            return filepath.read_text(encoding="utf-8")
        logger.error("WeChat content file not found: %s", filepath)
        return None

    return None


def parse_x_thread(content: str) -> list[str]:
    """Parse an X thread markdown file into a list of tweet strings.

    Supports two formats:
    1. Numbered lines starting with "N/" (e.g. "1/ Some text")
    2. Bold numbered headings "**N/M**" followed by tweet text
    """
    lines = content.strip().split("\n")
    tweets = []
    current_tweet = []
    in_tweet = False

    number_slash_re = re.compile(r"^(\d+)/\s+(.*)")
    bold_number_re = re.compile(r"^\*\*\d+/\d+\*\*\s*$")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") or stripped == "---" or stripped.startswith("> "):
            continue

        m = number_slash_re.match(stripped)
        if m:
            if current_tweet:
                tweets.append("\n".join(current_tweet).strip())
                current_tweet = []
            current_tweet.append(m.group(2))
            in_tweet = True
            continue

        if bold_number_re.match(stripped):
            if current_tweet:
                tweets.append("\n".join(current_tweet).strip())
                current_tweet = []
            in_tweet = True
            continue

        if in_tweet and stripped:
            current_tweet.append(stripped)

    if current_tweet:
        tweets.append("\n".join(current_tweet).strip())

    tweets = [t for t in tweets if t]
    return tweets


def _parse_markdown(content: str) -> tuple[str, str, str]:
    """Extract title, subtitle, and body from a Markdown article (Substack).

    Parsing rules:
        0. If YAML frontmatter exists, extract subtitle and title from it.
        1. First line starting with "# " is the title (text after "# ").
        2. The first bold line ("**...**") after the title is the subtitle.
        3. Everything after the title and subtitle lines is the body.

    Frontmatter subtitle takes precedence over inline bold subtitle.
    Frontmatter title is used as fallback if no H1 heading is found.

    Args:
        content: Raw Markdown content.

    Returns:
        Tuple of (title, subtitle, body).
    """
    lines = content.strip().split("\n")
    title = ""
    subtitle = ""
    body_start = 0

    # Step 0: Parse YAML frontmatter if present
    fm_subtitle = ""
    fm_title = ""
    content_start = 0
    if lines and lines[0].strip() == "---":
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
        if end_idx is not None:
            for line in lines[1:end_idx]:
                stripped = line.strip()
                fm_match = re.match(r'^subtitle:\s*["\']?(.+?)["\']?\s*$', stripped)
                if fm_match:
                    fm_subtitle = fm_match.group(1).strip()
                fm_title_match = re.match(r'^title:\s*["\']?(.+?)["\']?\s*$', stripped)
                if fm_title_match:
                    fm_title = fm_title_match.group(1).strip()
            content_start = end_idx + 1

    # Search for title in content (after frontmatter)
    for i in range(content_start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            body_start = i + 1
            break

    # Fallback to frontmatter title if no H1 found
    if not title and fm_title:
        title = fm_title

    # Find subtitle from first bold line after title
    if title:
        for i in range(body_start, min(body_start + 5, len(lines))):
            stripped = lines[i].strip()
            if not stripped:
                continue
            if stripped.startswith("**") and stripped.endswith("**"):
                inner = stripped[2:-2].strip()
                if inner and len(inner) < 200:
                    subtitle = inner
                    body_start = i + 1
                break
            elif stripped.startswith("**"):
                bold_match = re.match(r"\*\*(.+?)\*\*", stripped)
                if bold_match:
                    subtitle = bold_match.group(1)
                    body_start = i + 1
                break
            else:
                break

    # Frontmatter subtitle takes precedence if inline not found
    if not subtitle and fm_subtitle:
        subtitle = fm_subtitle

    # Body: everything from body_start onwards
    body = "\n".join(lines[body_start:]).strip()

    return title, subtitle, body


def load_env_file(filepath: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env = {}
    if not filepath.exists():
        return env
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("'\"")
    return env
