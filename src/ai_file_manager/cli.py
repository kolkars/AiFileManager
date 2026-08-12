from pathlib import Path
from typing import Annotated

import typer

from .config import Settings
from .database import create_database
from .discovery import discover_domains
from .extractors import default_registry
from .ingestion import IngestionService
from .models import Document
from .repository import DocumentRepository

app = typer.Typer(no_args_is_help=True, help="Index and search local knowledge files.")


def context() -> tuple[Settings, object]:
    settings = Settings.from_cwd()
    _engine, sessions = create_database(settings.database_path)
    return settings, sessions


@app.command()
def scan() -> None:
    settings, sessions = context()
    result = IngestionService(settings.knowledge_root, sessions, default_registry()).scan()
    typer.echo(f"new={result.new} changed={result.changed} unchanged={result.unchanged} deleted={result.deleted} errors={result.errors}")


@app.command()
def domains() -> None:
    settings, _sessions = context()
    for domain in discover_domains(settings.knowledge_root):
        typer.echo(domain)


@app.command("files")
def files_command(domain: str) -> None:
    _settings, sessions = context()
    with sessions() as session:
        for document in DocumentRepository(session).active(domain):
            typer.echo(f"{document.id}\t{document.relative_path}")


@app.command()
def show(file_id: int) -> None:
    _settings, sessions = context()
    with sessions() as session:
        document = session.get(Document, file_id)
        if document is None or document.is_deleted:
            raise typer.BadParameter(f"No active file with id {file_id}")
        typer.echo(f"Domain: {document.domain}\nPath: {document.relative_path}\nChecksum: {document.checksum}\nIndexed: {document.indexed_time.isoformat()}\n")
        typer.echo(document.text)


@app.command()
def search(domain: str, query: Annotated[str, typer.Argument(help="FTS5 query text")]) -> None:
    _settings, sessions = context()
    with sessions() as session:
        try:
            matches = DocumentRepository(session).search(domain, query)
        except Exception as error:
            raise typer.BadParameter(f"Invalid search query: {error}") from error
        for document in matches:
            typer.echo(f"{document.id}\t{document.relative_path}")


if __name__ == "__main__":
    app()
