import logging
from dataclasses import dataclass
from typing import Literal, Sequence
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db.database import get_database_url


logger = logging.getLogger("medtrek.documentation_chunks")

DocumentationChunkWriteStatus = Literal["inserted", "updated", "unchanged", "skipped"]


@dataclass(frozen=True)
class DocumentationChunkStorageRecord:
    chunk_id: str
    source_path: str
    title: str
    section_heading: str | None
    line_start: int
    line_end: int
    text: str
    character_count: int
    content_hash: str
    embedding_provider: str | None
    embedding_model: str | None
    embedding_dimension: int | None
    embedding_preview: list[float] | None
    embedding_status: str


@dataclass(frozen=True)
class DocumentationChunkWriteResult:
    chunk_id: str
    status: DocumentationChunkWriteStatus
    reason: str | None = None


class DocumentationChunksRepository:
    """Persist deterministic Dav AI documentation chunks.

    This repository stores metadata and deterministic preview embedding metadata
    only. It does not create vector columns, call embedding APIs, run retrieval,
    or participate in product safety workflows.
    """

    def _database_url(self) -> str | None:
        return get_database_url()

    def save_chunks(
        self,
        records: Sequence[DocumentationChunkStorageRecord],
    ) -> list[DocumentationChunkWriteResult]:
        database_url = self._database_url()

        if not database_url:
            return [
                DocumentationChunkWriteResult(
                    chunk_id=record.chunk_id,
                    status="skipped",
                    reason="database_not_configured",
                )
                for record in records
            ]

        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                return [self._save_chunk(cursor, record) for record in records]

    def _save_chunk(
        self,
        cursor,
        record: DocumentationChunkStorageRecord,
    ) -> DocumentationChunkWriteResult:
        cursor.execute(
            """
            select content_hash
            from documentation_chunks
            where chunk_id = %(chunk_id)s
            """,
            {"chunk_id": record.chunk_id},
        )
        existing_row = cursor.fetchone()

        if existing_row and existing_row["content_hash"] == record.content_hash:
            return DocumentationChunkWriteResult(
                chunk_id=record.chunk_id,
                status="unchanged",
            )

        params = {
            "chunk_id": record.chunk_id,
            "source_path": record.source_path,
            "title": record.title,
            "section_heading": record.section_heading,
            "line_start": record.line_start,
            "line_end": record.line_end,
            "text": record.text,
            "character_count": record.character_count,
            "content_hash": record.content_hash,
            "embedding_provider": record.embedding_provider,
            "embedding_model": record.embedding_model,
            "embedding_dimension": record.embedding_dimension,
            "embedding_preview": (
                Jsonb(record.embedding_preview)
                if record.embedding_preview is not None
                else None
            ),
            "embedding_status": record.embedding_status,
        }

        if existing_row:
            cursor.execute(
                """
                update documentation_chunks
                set
                    source_path = %(source_path)s,
                    title = %(title)s,
                    section_heading = %(section_heading)s,
                    line_start = %(line_start)s,
                    line_end = %(line_end)s,
                    text = %(text)s,
                    character_count = %(character_count)s,
                    content_hash = %(content_hash)s,
                    embedding_provider = %(embedding_provider)s,
                    embedding_model = %(embedding_model)s,
                    embedding_dimension = %(embedding_dimension)s,
                    embedding_preview = %(embedding_preview)s,
                    embedding_status = %(embedding_status)s,
                    updated_at = now()
                where chunk_id = %(chunk_id)s
                """,
                params,
            )
            return DocumentationChunkWriteResult(
                chunk_id=record.chunk_id,
                status="updated",
            )

        cursor.execute(
            """
            insert into documentation_chunks (
                id,
                chunk_id,
                source_path,
                title,
                section_heading,
                line_start,
                line_end,
                text,
                character_count,
                content_hash,
                embedding_provider,
                embedding_model,
                embedding_dimension,
                embedding_preview,
                embedding_status
            )
            values (
                %(id)s,
                %(chunk_id)s,
                %(source_path)s,
                %(title)s,
                %(section_heading)s,
                %(line_start)s,
                %(line_end)s,
                %(text)s,
                %(character_count)s,
                %(content_hash)s,
                %(embedding_provider)s,
                %(embedding_model)s,
                %(embedding_dimension)s,
                %(embedding_preview)s,
                %(embedding_status)s
            )
            """,
            {
                **params,
                "id": uuid4(),
            },
        )
        return DocumentationChunkWriteResult(
            chunk_id=record.chunk_id,
            status="inserted",
        )
