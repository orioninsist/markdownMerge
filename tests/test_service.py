"""End-to-end merge service tests."""

import json
import logging
from pathlib import Path

from markdown_merge.config import MergeConfig
from markdown_merge.service import MarkdownMergeService
from markdown_merge.tokenizer import TokenCounter


def test_service_creates_valid_token_limited_outputs(tmp_path: Path) -> None:
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"
    logs_directory = tmp_path / "logs"

    (input_directory / "api").mkdir(parents=True)
    logs_directory.mkdir()

    (input_directory / "intro.md").write_text(
        "# Introduction\n\n" + ("introductory text " * 600),
        encoding="utf-8",
    )
    (input_directory / "api" / "reference.md").write_text(
        "# API Reference\n\n" + ("reference documentation " * 1_500),
        encoding="utf-8",
    )

    log_path = logs_directory / "test.log"
    logger = logging.getLogger(f"test-service-{id(tmp_path)}")
    logger.handlers.clear()
    logger.addHandler(logging.FileHandler(log_path, encoding="utf-8"))
    logger.setLevel(logging.DEBUG)

    config = MergeConfig(
        input_directory=input_directory,
        output_directory=output_directory,
        project_root=tmp_path,
        token_limit=4_000,
        encoding_name="o200k_base",
        output_prefix="Test_Documentation",
        toc_reserve_tokens=500,
    )

    result = MarkdownMergeService(
        config=config,
        logger=logger,
        log_path=log_path,
    ).execute()

    counter = TokenCounter("o200k_base")

    assert result.output_parts
    assert result.manifest_path.exists()
    assert all(part.path.exists() for part in result.output_parts)

    for part in result.output_parts:
        text = part.path.read_text(encoding="utf-8")
        assert counter.count(text) <= 4_000
        assert "## Table of Contents" in text
        assert "## Source:" in text

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["token_limit"] == 4_000
    assert manifest["parts"]
