from __future__ import annotations

from markdown_merge.file_packer import FilePack
from markdown_merge.models import DocumentSegment


def file_packs_to_writer_parts(
    packs: list[FilePack],
) -> list[list[DocumentSegment]]:
    return [pack.segments for pack in packs]
