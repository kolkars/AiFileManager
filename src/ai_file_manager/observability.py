import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from .ingestion import ScanResult
from .models import Document, ScanRun


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(message)s")


def log_scan(result: ScanResult) -> None:
    logging.getLogger("ai_file_manager").info(json.dumps({"event": "scan_completed", **asdict(result)}, sort_keys=True))


def health_report(knowledge_root: Path, sessions) -> dict[str, object]:
    with sessions() as session:
        active = session.scalar(select(func.count()).select_from(Document).where(Document.is_deleted.is_(False))) or 0
        errors = session.scalar(select(func.count()).select_from(Document).where(Document.is_deleted.is_(False), Document.extraction_error.is_not(None))) or 0
        latest = session.scalar(select(ScanRun).order_by(ScanRun.id.desc()).limit(1))
        return {
            "status": "degraded" if errors else "ok",
            "checked_time": datetime.now(timezone.utc).isoformat(),
            "knowledge_root": str(knowledge_root),
            "knowledge_root_exists": knowledge_root.is_dir(),
            "active_documents": active,
            "documents_with_errors": errors,
            "last_scan_status": latest.status if latest else None,
            "last_scan_completed": latest.completed_time.isoformat() if latest and latest.completed_time else None,
        }
