from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .models import Document, DocumentVersion


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def by_key(self, domain: str, relative_path: str) -> Document | None:
        return self.session.scalar(select(Document).where(Document.domain == domain, Document.relative_path == relative_path))

    def active(self, domain: str | None = None) -> list[Document]:
        query = select(Document).where(Document.is_deleted.is_(False))
        if domain is not None:
            query = query.where(Document.domain == domain)
        return list(self.session.scalars(query.order_by(Document.domain, Document.relative_path)))

    def all_active_keys(self) -> dict[tuple[str, str], Document]:
        return {(doc.domain, doc.relative_path): doc for doc in self.active()}

    def sync_fts(self, document: Document) -> None:
        self.session.flush()
        self.session.execute(text("DELETE FROM documents_fts WHERE document_id = :id"), {"id": document.id})
        if not document.is_deleted:
            self.session.execute(
                text("INSERT INTO documents_fts(document_id, domain, content) VALUES (:id, :domain, :content)"),
                {"id": document.id, "domain": document.domain, "content": document.text},
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

    def search(self, domain: str, query: str) -> list[Document]:
        # Search accepts ordinary user text rather than raw FTS5 syntax.
        normalized = query.strip()
        while len(normalized) >= 2 and normalized.startswith('"') and normalized.endswith('"'):
            normalized = normalized[1:-1].strip()
        if not normalized:
            return []
        fts_query = f'"{normalized.replace(chr(34), chr(34) * 2)}"'
        ids = self.session.execute(
            text("SELECT document_id FROM documents_fts WHERE domain = :domain AND documents_fts MATCH :query ORDER BY rank"),
            {"domain": domain, "query": fts_query},
        ).scalars()
        result: list[Document] = []
        for document_id in ids:
            document = self.session.get(Document, int(document_id))
            if document is not None and not document.is_deleted:
                result.append(document)
        return result
