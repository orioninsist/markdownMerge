"""Token-aware Markdown merger."""

from markdown_merge.config import MergeConfig
from markdown_merge.models import MergeResult
from markdown_merge.service import MarkdownMergeService

__all__ = ["MarkdownMergeService", "MergeConfig", "MergeResult"]
__version__ = "1.0.0"
