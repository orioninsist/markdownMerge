"""Tests for shared domain models."""

from markdown_merge.models import ProgressUpdate


def test_progress_update_carries_structured_telemetry() -> None:
    update = ProgressUpdate(
        stage="Packing token-limited outputs",
        completed=12,
        total=40,
        detail="Packing source segments",
        current_source="api/responses.md",
        current_part=3,
        current_tokens=125_000,
        token_limit=150_000,
    )

    assert update.completed == 12
    assert update.total == 40
    assert update.current_source == "api/responses.md"
    assert update.current_part == 3
    assert update.current_tokens == 125_000
    assert update.token_limit == 150_000
