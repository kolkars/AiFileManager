import json

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from .extractors.base import ContentUnit
from .models import Document, DocumentExtraction, DocumentUnit, DocumentVersion


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def by_key(self, domain: str, relative_path: str) -> Document | None:
        return self.session.scalar(
            select(Document).where(
                Document.domain == domain,
                Document.relative_path == relative_path,
            )
        )

    def active(self, domain: str | None = None) -> list[Document]:
        query = select(Document).where(Document.is_deleted.is_(False))
        if domain is not None:
            query = query.where(Document.domain == domain)
        return list(
            self.session.scalars(
                query.order_by(Document.domain, Document.relative_path)
            )
        )

    def all_active_keys(self) -> dict[tuple[str, str], Document]:
        return {(document.domain, document.relative_path): document for document in self.active()}

    def sync_fts(self, document: Document) -> None:
        self.session.flush()
        self.session.execute(
            text("DELETE FROM documents_fts WHERE document_id = :id"),
            {"id": document.id},
        )
        if not document.is_deleted:
            self.session.execute(
                text(
                    "INSERT INTO documents_fts(document_id, domain, content) "
                    "VALUES (:id, :domain, :content)"
                ),
                {
                    "id": document.id,
                    "domain": document.domain,
                    "content": document.text,
                },
            )

    def record_version(self, document: Document) -> None:
        self.session.flush()
        exists = self.session.scalar(
            select(DocumentVersion.id).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.checksum == document.checksum,
            )
        )
        if exists is None:
            self.session.add(
                DocumentVersion(
                    document_id=document.id,
                    checksum=document.checksum,
                    size=document.size,
                    modified_time=document.modified_time,
                    indexed_time=document.indexed_time,
                    text=document.text,
                    extraction_error=document.extraction_error,
                )
            )

    def replace_units(
        self,
        document: Document,
        units: tuple[ContentUnit, ...],
    ) -> None:
        self.session.flush()
        self.session.execute(
            delete(DocumentUnit).where(DocumentUnit.document_id == document.id)
        )
        self.session.add_all(
            DocumentUnit(
                document_id=document.id,
                kind=unit.kind,
                ordinal=unit.ordinal,
                text=unit.text,
                location=unit.location,
                metadata_json=json.dumps(unit.metadata, sort_keys=True),
            )
            for unit in units
        )

    def replace_extraction_metadata(
        self,
        document: Document,
        metadata: dict[str, object],
    ) -> None:
        self.session.flush()
        value = self.session.get(DocumentExtraction, document.id)
        metadata_json = json.dumps(metadata, sort_keys=True)
        if value is None:
            self.session.add(
                DocumentExtraction(
                    document_id=document.id,
                    metadata_json=metadata_json,
                )
            )
        else:
            value.metadata_json = metadata_json

    def search(
        self,
        domain: str,
        query: str,
        extension: str | None = None,
    ) -> list[Document]:
        normalized = query.strip()
        while (
            len(normalized) >= 2
            and normalized.startswith('"')
            and normalized.endswith('"')
        ):
            normalized = normalized[1:-1].strip()
        if not normalized:
            return []

        escaped = normalized.replace('"', '""')
        fts_query = f'"{escaped}"'
        document_ids = self.session.execute(
            text(
                "SELECT document_id FROM documents_fts "
                "WHERE domain = :domain AND documents_fts MATCH :query "
                "ORDER BY rank"
            ),
            {"domain": domain, "query": fts_query},
        ).scalars()

        normalized_extension = extension.lower() if extension is not None else None
        result: list[Document] = []
        for document_id in document_ids:
            document = self.session.get(Document, int(document_id))
            if document is None or document.is_deleted:
                continue
            if (
                normalized_extension is not None
                and document.extension != normalized_extension
            ):
                continue
            result.append(document)
        return result
