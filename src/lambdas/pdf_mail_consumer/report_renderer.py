"""Renderers for HTML, text and PDF report payloads."""

from decimal import Decimal
from html import escape
import json
import textwrap
from typing import Any, Dict, List, Sequence


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, set):
        return sorted(value)
    return str(value)


def _format_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default)


def _build_summary_lines(report: Dict[str, Any]) -> List[str]:
    result = report.get("result", {}) or {}
    lines = [
        f"Execution ID: {report.get('execution_id', '')}",
        f"Email: {report.get('email', '')}",
        f"Prompt: {report.get('prompt', '') or 'Sem prompt informado'}",
        f"Source image: {report.get('image', '') or 'Not provided'}",
        "",
        "Analysis result:",
    ]

    result_json = _format_json(result)
    for raw_line in result_json.splitlines() or ["{}"]:
        wrapped_lines = textwrap.wrap(
            raw_line,
            width=92,
            drop_whitespace=False,
            replace_whitespace=False,
            break_long_words=False,
            break_on_hyphens=False,
        )
        lines.extend(wrapped_lines or [""])

    return lines


def build_text_report(report: Dict[str, Any], download_url: str) -> str:
    lines = [
        "Architecture analysis report",
        "",
        f"Download PDF: {download_url}",
        "",
    ]
    lines.extend(_build_summary_lines(report))
    return "\n".join(lines)


def build_html_report(report: Dict[str, Any], download_url: str) -> str:
    result_json = _format_json(report.get("result", {}) or {})
    execution_id = escape(str(report.get("execution_id", "")))
    email = escape(str(report.get("email", "")))
    prompt = escape(str(report.get("prompt") or "Sem prompt informado"))
    image = escape(str(report.get("image") or "Not provided"))
    download_link = escape(download_url)

    return f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <style>
      body {{
        margin: 0;
        padding: 0;
        background: #f3efe7;
        color: #1f2937;
        font-family: Arial, Helvetica, sans-serif;
      }}
      .shell {{
        max-width: 760px;
        margin: 0 auto;
        padding: 32px 20px 40px;
      }}
      .card {{
        background: #ffffff;
        border: 1px solid #e5ded0;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 18px 50px rgba(17, 24, 39, 0.08);
      }}
      .hero {{
        padding: 28px 28px 20px;
        background: linear-gradient(135deg, #1f3a5f 0%, #0f766e 100%);
        color: #fff;
      }}
      .hero h1 {{ margin: 0 0 8px; font-size: 26px; line-height: 1.2; }}
      .hero p {{ margin: 0; opacity: 0.92; }}
      .content {{ padding: 28px; }}
      .meta {{ display: grid; gap: 14px; margin-bottom: 24px; }}
      .meta-item {{
        padding: 14px 16px;
        background: #faf7f0;
        border-radius: 14px;
        border: 1px solid #ece3d2;
      }}
      .meta-item strong {{ display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #6b7280; margin-bottom: 6px; }}
      .download {{
        display: inline-block;
        padding: 12px 18px;
        border-radius: 999px;
        background: #0f766e;
        color: #fff !important;
        text-decoration: none;
        font-weight: 700;
        margin-bottom: 24px;
      }}
      pre {{
        margin: 0;
        padding: 20px;
        border-radius: 16px;
        background: #0b1020;
        color: #e5e7eb;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 13px;
        line-height: 1.6;
      }}
      .footer {{
        margin-top: 18px;
        font-size: 12px;
        color: #6b7280;
      }}
    </style>
  </head>
  <body>
    <div class=\"shell\">
      <div class=\"card\">
        <div class=\"hero\">
          <h1>Architecture analysis report</h1>
          <p>The report is available in S3.</p>
        </div>
        <div class=\"content\">
          <a class=\"download\" href=\"{download_link}\">Download PDF</a>
          <div class=\"meta\">
            <div class=\"meta-item\"><strong>Execution ID</strong>{execution_id}</div>
            <div class=\"meta-item\"><strong>Email</strong>{email}</div>
            <div class=\"meta-item\"><strong>Prompt</strong>{prompt}</div>
            <div class=\"meta-item\"><strong>Source image</strong>{image}</div>
          </div>
          <pre>{escape(result_json)}</pre>
          <div class=\"footer\">If the link expires, request a new analysis e-mail to receive a refreshed download URL.</div>
        </div>
      </div>
    </div>
  </body>
</html>"""


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _build_pdf_content(lines: Sequence[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", "50 760 Td"]
    for index, line in enumerate(lines):
        if index > 0:
            commands.append("0 -13 Td")
        commands.append(f"({_escape_pdf_text(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1")


def _chunk_lines(lines: Sequence[str], chunk_size: int) -> List[List[str]]:
    return [list(lines[index : index + chunk_size]) for index in range(0, len(lines), chunk_size)]


def _write_pdf_object(buffer: bytearray, object_number: int, body: bytes, offsets: List[int]) -> None:
    offsets.append(len(buffer))
    buffer.extend(f"{object_number} 0 obj\n".encode("ascii"))
    buffer.extend(body)
    buffer.extend(b"\nendobj\n")


def build_pdf_report(report: Dict[str, Any]) -> bytes:
    lines = _build_summary_lines(report)
    if not lines:
        lines = ["Architecture analysis report"]

    pages = _chunk_lines(lines, 46)
    object_count = 3 + len(pages) * 2
    page_object_numbers = [4 + index * 2 for index in range(len(pages))]
    content_object_numbers = [5 + index * 2 for index in range(len(pages))]

    buffer = bytearray(b"%PDF-1.4\n")
    offsets: List[int] = []

    _write_pdf_object(buffer, 1, b"<< /Type /Catalog /Pages 2 0 R >>", offsets)

    kids = " ".join(f"{page_number} 0 R" for page_number in page_object_numbers)
    pages_body = f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("ascii")
    _write_pdf_object(buffer, 2, pages_body, offsets)

    _write_pdf_object(
        buffer,
        3,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        offsets,
    )

    for page_number, content_number, page_lines in zip(page_object_numbers, content_object_numbers, pages):
        content_bytes = _build_pdf_content(page_lines or [""])
        content_body = b"<< /Length " + str(len(content_bytes)).encode("ascii") + b" >>\nstream\n" + content_bytes + b"\nendstream"
        _write_pdf_object(buffer, content_number, content_body, offsets)

        page_body = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>"
        ).encode("ascii")
        _write_pdf_object(buffer, page_number, page_body, offsets)

    xref_start = len(buffer)
    buffer.extend(f"xref\n0 {object_count + 1}\n".encode("ascii"))
    buffer.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        buffer.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    buffer.extend(
        (
            f"trailer\n<< /Size {object_count + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(buffer)
