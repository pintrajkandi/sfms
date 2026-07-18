"""
Tabular export helpers — CSV and XLSX (accountants live in Excel).

    return export_response("xlsx", "defaulters", ["Name", "Due"], rows)
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Sequence

from django.http import HttpResponse

from apps.core.logging import ctx, get_logger

log = get_logger("exports")


def csv_response(filename: str, headers: Sequence[str], rows: Iterable[Sequence]) -> HttpResponse:
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
    writer = csv.writer(resp)
    writer.writerow(headers)
    writer.writerows(rows)
    return resp


def xlsx_response(filename: str, headers: Sequence[str], rows: Iterable[Sequence]) -> HttpResponse:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31]
    ws.append(list(headers))
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(list(row))
    for i, _ in enumerate(headers, start=1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else "AA"].width = 20

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    resp = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return resp


def export_response(
    fmt: str, filename: str, headers: Sequence[str], rows: Iterable[Sequence]
) -> HttpResponse:
    rows = list(rows)
    log.info(
        "export generated file=%s fmt=%s rows=%s",
        filename,
        fmt,
        len(rows),
        **ctx(action="export"),
    )
    if fmt == "xlsx":
        return xlsx_response(filename, headers, rows)
    return csv_response(filename, headers, rows)
