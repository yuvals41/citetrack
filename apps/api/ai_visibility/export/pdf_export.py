from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _pdf_output_bytes(pdf: Any) -> bytes:
    output = pdf.output(dest="S")
    if isinstance(output, bytes):
        return output
    if isinstance(output, bytearray):
        return bytes(output)
    return str(output).encode("latin-1", errors="replace")


def _safe_text(value: object) -> str:
    return str(value or "").replace("\u2014", "-")


def _coalesce(data: list[dict[str, object]], key: str, default: str = "") -> str:
    for item in data:
        if key in item and item.get(key) not in (None, ""):
            return _safe_text(item.get(key))
    return default


def _new_pdf(title: str) -> Any:
    fpdf_module = __import__("fpdf", fromlist=["FPDF"])
    FPDF = getattr(fpdf_module, "FPDF")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _safe_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 8, f"Generated: {generated}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    return pdf


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _minimal_pdf(lines: list[str]) -> bytes:
    y = 780
    commands: list[str] = ["BT", "/F1 11 Tf"]
    for line in lines:
        commands.append(f"72 {y} Td ({_escape_pdf_text(_safe_text(line))}) Tj")
        y -= 16
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1"))
    return bytes(pdf)


def _table_header(pdf: Any, headers: list[str], widths: list[float]) -> None:
    pdf.set_font("Helvetica", "B", 10)
    for header, width in zip(headers, widths):
        pdf.cell(width, 8, _safe_text(header), border=1)
    pdf.ln()


def _table_row(pdf: Any, values: list[str], widths: list[float]) -> None:
    pdf.set_font("Helvetica", size=9)
    for value, width in zip(values, widths):
        text = _safe_text(value)
        if len(text) > 64:
            text = f"{text[:61]}..."
        pdf.cell(width, 7, text, border=1)
    pdf.ln()


async def generate_dashboard_pdf(data: list[dict[str, object]], workspace_name: str) -> bytes:
    normalized_data = data
    try:
        pdf = _new_pdf(f"AI Visibility Report - {workspace_name}")
    except ModuleNotFoundError:
        lines = [
            f"AI Visibility Report - {workspace_name}",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Visibility Score: {_coalesce(normalized_data, 'visibility_score', '0%')}",
            f"Citation Coverage: {_coalesce(normalized_data, 'citation_coverage', '0%')}",
        ]
        return _minimal_pdf(lines)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary Metrics", new_x="LMARGIN", new_y="NEXT")
    _table_header(pdf, ["Metric", "Value"], [70, 120])
    summary_rows = [
        ["Visibility Score", _coalesce(normalized_data, "visibility_score", "0%")],
        ["Citation Coverage", _coalesce(normalized_data, "citation_coverage", "0%")],
        ["Average Position", _coalesce(normalized_data, "position", _coalesce(normalized_data, "avg_position", "0"))],
        ["Sentiment", _coalesce(normalized_data, "sentiment", "n/a")],
    ]
    for summary_row in summary_rows:
        _table_row(pdf, summary_row, [70, 120])

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Scan History", new_x="LMARGIN", new_y="NEXT")
    _table_header(pdf, ["Provider", "Status", "Model", "Created At"], [40, 35, 55, 60])

    if not normalized_data:
        _table_row(pdf, ["-", "-", "-", "No scans"], [40, 35, 55, 60])
    else:
        for scan_row in normalized_data[:50]:
            _table_row(
                pdf,
                [
                    _safe_text(scan_row.get("provider", "")),
                    _safe_text(scan_row.get("status", "")),
                    _safe_text(scan_row.get("model", "")),
                    _safe_text(scan_row.get("created_at", "")),
                ],
                [40, 35, 55, 60],
            )

    return _pdf_output_bytes(pdf)


async def generate_responses_pdf(data: list[dict[str, object]], workspace_name: str) -> bytes:
    normalized_data = data
    try:
        pdf = _new_pdf(f"AI Responses Report - {workspace_name}")
    except ModuleNotFoundError:
        lines = [
            f"AI Responses Report - {workspace_name}",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Responses: {len(normalized_data)}",
        ]
        return _minimal_pdf(lines)

    _table_header(pdf, ["Provider", "Question", "Status", "Citation URL"], [28, 68, 24, 90])

    if not normalized_data:
        _table_row(pdf, ["-", "No responses", "-", "-"], [28, 68, 24, 90])
    else:
        for row in normalized_data[:100]:
            _table_row(
                pdf,
                [
                    _safe_text(row.get("provider", "")),
                    _safe_text(row.get("prompt_text", "")),
                    _safe_text(row.get("mention_type", "")),
                    _safe_text(row.get("citation_url", "")),
                ],
                [28, 68, 24, 90],
            )

    return _pdf_output_bytes(pdf)
