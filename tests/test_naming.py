"""Tests for generic content-aware output naming."""

from pathlib import Path

from markdown_merge.naming import derive_output_prefix


def test_combines_directory_identity_with_repeated_heading_phrase(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "instagram"
    input_directory.mkdir()

    first = input_directory / "account.md"
    second = input_directory / "privacy.md"
    third = input_directory / "security.md"

    first.write_text(
        "# Instagram Help Center\n\nAccount information.",
        encoding="utf-8",
    )
    second.write_text(
        "# Instagram Help Center\n\nPrivacy information.",
        encoding="utf-8",
    )
    third.write_text(
        "# Instagram Help Center\n\nSecurity information.",
        encoding="utf-8",
    )

    result = derive_output_prefix(
        input_directory,
        [first, second, third],
    )

    assert result == "Instagram_Help_Center"


def test_works_for_an_unrelated_api_documentation_corpus(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "acme"
    input_directory.mkdir()

    first = input_directory / "users.md"
    second = input_directory / "orders.md"

    first.write_text(
        "# API Reference\n\nUsers endpoint.",
        encoding="utf-8",
    )
    second.write_text(
        "# API Reference\n\nOrders endpoint.",
        encoding="utf-8",
    )

    result = derive_output_prefix(
        input_directory,
        [first, second],
    )

    assert result == "Acme_API_Reference"


def test_uses_content_when_directory_name_is_generic(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "docs"
    input_directory.mkdir()

    first = input_directory / "install.md"
    second = input_directory / "config.md"

    first.write_text(
        "# Product User Guide\n\nInstallation.",
        encoding="utf-8",
    )
    second.write_text(
        "# Product User Guide\n\nConfiguration.",
        encoding="utf-8",
    )

    result = derive_output_prefix(
        input_directory,
        [first, second],
    )

    assert result == "Product_User_Guide"


def test_does_not_contain_a_hardcoded_brand(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "sample-project"
    input_directory.mkdir()

    source = input_directory / "overview.md"
    source.write_text(
        "# Deployment Manual\n\nGeneral deployment instructions.",
        encoding="utf-8",
    )

    result = derive_output_prefix(
        input_directory,
        [source],
    )

    assert result.startswith("Sample_Project")
    assert "OpenAI" not in result
    assert "Instagram" not in result


def test_uses_generic_fallback_when_no_identity_or_titles_exist(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "docs"
    input_directory.mkdir()

    source = input_directory / "empty.md"
    source.write_text("", encoding="utf-8")

    result = derive_output_prefix(
        input_directory,
        [source],
    )

    assert result == "Merged_Markdown"


def test_preserves_known_acronyms_without_duplicates(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "acme-api"
    input_directory.mkdir()

    source = input_directory / "reference.md"
    source.write_text(
        "# API Reference\n\nEndpoint documentation.",
        encoding="utf-8",
    )

    result = derive_output_prefix(
        input_directory,
        [source],
    )

    assert result == "Acme_API_Reference"
    assert "API_API" not in result
