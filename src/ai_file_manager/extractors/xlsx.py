from pathlib import Path

from openpyxl import load_workbook


class XlsxExtractor:
    def extract(self, path: Path) -> str:
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            lines: list[str] = []
            for sheet in workbook.worksheets:
                lines.append(sheet.title)
                lines.extend("\t".join("" if value is None else str(value) for value in row) for row in sheet.iter_rows(values_only=True))
            return "\n".join(lines)
        finally:
            workbook.close()

