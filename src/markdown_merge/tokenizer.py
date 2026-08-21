"""Exact token counting and token-safe splitting."""

from __future__ import annotations

from collections.abc import Sequence

import tiktoken
from tiktoken.core import Encoding


class TokenCounter:
    """Count and split text using a configured tiktoken encoding."""

    def __init__(self, encoding_name: str) -> None:
        try:
            self._encoding: Encoding = tiktoken.get_encoding(encoding_name)
        except ValueError as error:
            raise ValueError(f"Unknown tiktoken encoding: {encoding_name}") from error

    @property
    def encoding_name(self) -> str:
        """Return the active encoding name."""
        return self._encoding.name

    def count(self, text: str) -> int:
        """Return the exact token count for text."""
        return len(self._encoding.encode(text, disallowed_special=()))

    def encode(self, text: str) -> list[int]:
        """Encode text into token IDs."""
        return self._encoding.encode(text, disallowed_special=())

    def decode(self, token_ids: Sequence[int]) -> str:
        """Decode token IDs back into text."""
        return self._encoding.decode(list(token_ids))
