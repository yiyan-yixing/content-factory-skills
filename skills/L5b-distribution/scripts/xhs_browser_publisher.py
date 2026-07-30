"""Thin re-export wrapper for xhs_browser_publisher.

This module re-exports the canonical implementation from
biz.content.publish.xhs_browser_publisher so the skill scripts/
directory can import it directly.
"""

from biz.content.publish.xhs_browser_publisher import XhsBrowserPublisher  # noqa: F401

__all__ = ["XhsBrowserPublisher"]
