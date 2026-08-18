"""Renderers for HTML, text and PDF report payloads."""

from decimal import Decimal
from html import escape
import json
import os
import struct
import textwrap
from typing import Any, Dict, List, Sequence
import zlib
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, set):
        return sorted(value)
    return str(value)


def _format_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default)


def _normalize_dynamodb_value(value: Any) -> Any:
    if isinstance(value, dict):
        if len(value) == 1:
            key = next(iter(value))
            nested_value = value[key]

            if key == "S":
                return nested_value
            if key == "N":
                return Decimal(nested_value)
            if key == "BOOL":
                return bool(nested_value)
            if key == "NULL":
                return None
            if key == "M":
                return {
                    nested_key: _normalize_dynamodb_value(nested_item)
                    for nested_key, nested_item in nested_value.items()
                }
            if key == "L":
                return [_normalize_dynamodb_value(item) for item in nested_value]
            if key == "SS":
                return list(nested_value)
            if key == "NS":
                return [Decimal(item) for item in nested_value]
            if key == "BS":
                return list(nested_value)

        return {
            nested_key: _normalize_dynamodb_value(nested_item)
            for nested_key, nested_item in value.items()
        }

    if isinstance(value, list):
        return [_normalize_dynamodb_value(item) for item in value]

    return value


def _parse_s3_uri(s3_uri: str) -> tuple[str, str] | None:
    if not isinstance(s3_uri, str) or not s3_uri.startswith("s3://"):
        return None

    bucket_and_key = s3_uri[5:]
    bucket, _, key = bucket_and_key.partition("/")
    if not bucket or not key:
        return None
    return bucket, key


def _create_image_url(s3_uri: str) -> str:
    parsed = _parse_s3_uri(s3_uri)
    if not parsed:
        return s3_uri

    bucket, key = parsed
    region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )
    s3_client = boto3.client("s3", region_name=region)

    try:
        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=86400,
        )
    except ClientError:
        return s3_uri


def _fetch_s3_object_bytes(s3_uri: str) -> bytes | None:
    parsed = _parse_s3_uri(s3_uri)
    if not parsed:
        return None

    bucket, key = parsed
    region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )
    s3_client = boto3.client("s3", region_name=region)

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()
        return body or None
    except (ClientError, BotoCoreError):
        return None


def _paeth_predictor(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    left_distance = abs(estimate - left)
    above_distance = abs(estimate - above)
    upper_left_distance = abs(estimate - upper_left)

    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def _apply_png_filter(
    filter_type: int, row: bytes, previous_row: bytes, bytes_per_pixel: int
) -> bytes:
    output = bytearray(len(row))

    for index, value in enumerate(row):
        left = output[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        above = previous_row[index] if previous_row else 0
        upper_left = (
            previous_row[index - bytes_per_pixel]
            if previous_row and index >= bytes_per_pixel
            else 0
        )

        if filter_type == 0:
            decoded = value
        elif filter_type == 1:
            decoded = (value + left) & 0xFF
        elif filter_type == 2:
            decoded = (value + above) & 0xFF
        elif filter_type == 3:
            decoded = (value + ((left + above) // 2)) & 0xFF
        elif filter_type == 4:
            decoded = (value + _paeth_predictor(left, above, upper_left)) & 0xFF
        else:
            raise ValueError(f"Unsupported PNG filter: {filter_type}")

        output[index] = decoded

    return bytes(output)


def _decode_png_to_rgb(image_bytes: bytes) -> Dict[str, Any] | None:
    png_signature = b"\x89PNG\r\n\x1a\n"
    if not image_bytes.startswith(png_signature):
        return None

    offset = len(png_signature)
    MAX_EMBED_PIXELS = int(os.environ.get("AUTOARCH_PDF_MAX_PIXELS", "1000000"))
    width = height = bit_depth = color_type = interlace = None
    palette = b""
    transparency = b""
    compressed_chunks: List[bytes] = []

    while offset + 8 <= len(image_bytes):
        chunk_length = struct.unpack(">I", image_bytes[offset : offset + 4])[0]
        offset += 4
        chunk_type = image_bytes[offset : offset + 4]
        offset += 4
        chunk_data = image_bytes[offset : offset + chunk_length]
        offset += chunk_length + 4

        if chunk_type == b"IHDR":
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", chunk_data)
            if compression != 0 or filter_method != 0:
                return None
            # avoid decoding very large images into memory which can cause Lambda OOM
            try:
                if width * height > MAX_EMBED_PIXELS:
                    logging.getLogger(__name__).warning(
                        "Skipping embedding image into PDF because dimensions too large: %dx%d > %d",
                        width,
                        height,
                        MAX_EMBED_PIXELS,
                    )
                    return None
            except Exception:
                # be defensive: if any parsing error occurs, skip image embedding
                return None
        elif chunk_type == b"PLTE":
            palette = chunk_data
        elif chunk_type == b"tRNS":
            transparency = chunk_data
        elif chunk_type == b"IDAT":
            compressed_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if not width or not height or bit_depth != 8 or interlace != 0:
        return None

    try:
        decompressed = zlib.decompress(b"".join(compressed_chunks))
    except zlib.error:
        return None

    if color_type == 0:
        bytes_per_pixel = 1
    elif color_type == 2:
        bytes_per_pixel = 3
    elif color_type == 3:
        bytes_per_pixel = 1
    elif color_type == 4:
        bytes_per_pixel = 2
    elif color_type == 6:
        bytes_per_pixel = 4
    else:
        return None

    row_stride = width * bytes_per_pixel
    expected_length = (row_stride + 1) * height
    if len(decompressed) < expected_length:
        return None

    previous_row = b""
    rgb_rows = bytearray()
    cursor = 0

    for _row_index in range(height):
        filter_type = decompressed[cursor]
        cursor += 1
        row_data = decompressed[cursor : cursor + row_stride]
        cursor += row_stride
        decoded_row = _apply_png_filter(
            filter_type, row_data, previous_row, bytes_per_pixel
        )
        previous_row = decoded_row

        if color_type == 0:
            for pixel in decoded_row:
                rgb_rows.extend((pixel, pixel, pixel))
        elif color_type == 2:
            rgb_rows.extend(decoded_row)
        elif color_type == 3:
            for index in decoded_row:
                palette_offset = index * 3
                if palette_offset + 3 > len(palette):
                    return None
                red, green, blue = palette[palette_offset : palette_offset + 3]
                alpha = transparency[index] if index < len(transparency) else 255
                rgb_rows.extend(
                    (
                        (red * alpha + 255 * (255 - alpha)) // 255,
                        (green * alpha + 255 * (255 - alpha)) // 255,
                        (blue * alpha + 255 * (255 - alpha)) // 255,
                    )
                )
        elif color_type == 4:
            for offset_index in range(0, len(decoded_row), 2):
                gray = decoded_row[offset_index]
                alpha = decoded_row[offset_index + 1]
                composite = (gray * alpha + 255 * (255 - alpha)) // 255
                rgb_rows.extend((composite, composite, composite))
        elif color_type == 6:
            for offset_index in range(0, len(decoded_row), 4):
                red = decoded_row[offset_index]
                green = decoded_row[offset_index + 1]
                blue = decoded_row[offset_index + 2]
                alpha = decoded_row[offset_index + 3]
                rgb_rows.extend(
                    (
                        (red * alpha + 255 * (255 - alpha)) // 255,
                        (green * alpha + 255 * (255 - alpha)) // 255,
                        (blue * alpha + 255 * (255 - alpha)) // 255,
                    )
                )

    return {
        "width": width,
        "height": height,
        "data": zlib.compress(bytes(rgb_rows)),
        "color_space": "/DeviceRGB",
        "bits": 8,
    }


def _build_pdf_image_resource(image_uri: Any) -> Dict[str, Any] | None:
    if not isinstance(image_uri, str):
        return None

    image_bytes = _fetch_s3_object_bytes(image_uri)
    if not image_bytes:
        return None

    return _decode_png_to_rgb(image_bytes)


def _format_title(value: Any) -> str:
    text = str(value).replace("_", " ").replace("-", " ").strip()
    return text.title() if text else "Detalhe"


def _format_scalar(value: Any) -> str:
    if value is None:
        return "Não informado"
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, Decimal):
        return str(int(value) if value == value.to_integral_value() else float(value))
    if isinstance(value, (dict, list, tuple, set)):
        return _format_json(value)
    return str(value)


def _build_result_lines(value: Any, lines: List[str], indent: int = 0) -> None:
    prefix = "  " * indent

    if isinstance(value, dict):
        if not value:
            lines.append(f"{prefix}Sem informações")
            return

        for key, nested_value in value.items():
            lines.append(f"{prefix}{_format_title(key)}:")
            _build_result_lines(nested_value, lines, indent + 1)
        return

    if isinstance(value, (list, tuple, set)):
        items = list(value)
        if not items:
            lines.append(f"{prefix}Sem itens")
            return

        for item in items:
            if isinstance(item, (dict, list, tuple, set)):
                _build_result_lines(item, lines, indent + 1)
            else:
                lines.append(f"{prefix}- {_format_scalar(item)}")
        return

    lines.append(f"{prefix}{_format_scalar(value)}")


def _build_result_html(value: Any, heading_level: int = 3) -> str:
    if isinstance(value, dict):
        if not value:
            return '<p class="result-empty">Sem informações.</p>'

        sections = []
        for key, nested_value in value.items():
            sections.append(
                f'<section class="result-section">'
                f"<h{heading_level}>{escape(_format_title(key))}</h{heading_level}>"
                f"{_build_result_html(nested_value, min(heading_level + 1, 5))}"
                f"</section>"
            )
        return "".join(sections)

    if isinstance(value, (list, tuple, set)):
        items = list(value)
        if not items:
            return '<p class="result-empty">Sem itens.</p>'

        rendered_items = []
        for item in items:
            if isinstance(item, (dict, list, tuple, set)):
                rendered_items.append(
                    f"<li>{_build_result_html(item, min(heading_level + 1, 5))}</li>"
                )
            else:
                rendered_items.append(f"<li>{escape(_format_scalar(item))}</li>")
        return f'<ul class="result-list">{"".join(rendered_items)}</ul>'

    return f'<p class="result-value">{escape(_format_scalar(value))}</p>'


def _build_summary_lines(report: Dict[str, Any]) -> List[str]:
    normalized = _normalize_dynamodb_value(report)
    result = normalized.get("result", {}) or {}
    lines = [
        f"Email: {normalized.get('email', '')}",
        f"Prompt: {normalized.get('prompt', '') or 'Sem prompt informado'}",
        f"Imagem enviada: {normalized.get('image', '') or 'Não informado'}",
        "",
        "Relatório da IA:",
    ]

    _build_result_lines(result, lines)
    return lines


def build_text_report(report: Dict[str, Any], download_url: str) -> str:
    lines = [
        "Architecture analysis report",
        "",
        f"Link de download do resultado: {download_url}",
        "",
    ]
    lines.extend(_build_summary_lines(report))
    return "\n".join(lines)


def build_html_report(report: Dict[str, Any], download_url: str) -> str:
    normalized = _normalize_dynamodb_value(report)
    email = escape(str(normalized.get("email", "")))
    prompt = escape(str(normalized.get("prompt") or "Sem prompt informado"))
    image = escape(str(normalized.get("image") or "Não informado"))
    image_source = _create_image_url(str(normalized.get("image") or ""))
    image_source_escaped = escape(image_source)
    download_link = escape(download_url)
    result = normalized.get("result", {}) or {}
    technical_analysis = (
        result.get("technical_analysis") if isinstance(result, dict) else None
    )
    if technical_analysis is None:
        technical_analysis = result
    result_html = (
        '<section class="result-section">'
        "<h3>Technical Analysis</h3>"
        f"{_build_result_html(technical_analysis, 4)}"
        "</section>"
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
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
      .meta-link {{ color: #0f766e; word-break: break-all; }}
            .image-preview {{
                margin-top: 10px;
            }}
            .image-preview img {{
                display: block;
                width: 100%;
                max-width: 640px;
                height: auto;
                border-radius: 12px;
                border: 1px solid #d6d3d1;
                background: #fff;
            }}
            .image-preview a {{
                display: inline-block;
                margin-top: 8px;
                color: #0f766e;
                word-break: break-all;
            }}
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
      .result {{ display: grid; gap: 16px; }}
      .result-section {{
        padding: 16px 18px;
        border-radius: 16px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
      }}
      .result-section h3,
      .result-section h4,
      .result-section h5 {{
        margin: 0 0 10px;
        color: #0f172a;
        line-height: 1.25;
      }}
      .result-section h3 {{ font-size: 18px; }}
      .result-section h4 {{ font-size: 16px; }}
      .result-section h5 {{ font-size: 14px; }}
      .result-value {{
        margin: 0;
        color: #1f2937;
        line-height: 1.7;
        white-space: pre-wrap;
        word-break: break-word;
      }}
      .result-list {{
        margin: 0;
        padding-left: 20px;
        color: #1f2937;
        line-height: 1.7;
      }}
      .result-empty {{ margin: 0; color: #6b7280; }}
      .footer {{ margin-top: 18px; font-size: 12px; color: #6b7280; }}
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="card">
        <div class="hero">
          <h1>Architecture analysis report</h1>
          <p>The report is available in S3.</p>
        </div>
        <div class="content">
          <a class="download" href="{download_link}">Link de download do resultado</a>
          <div class="meta">
            <div class="meta-item"><strong>Email</strong>{email}</div>
            <div class="meta-item"><strong>Prompt</strong>{prompt}</div>
                        <div class="meta-item">
                            <strong>Imagem enviada para análise</strong>
                            <div class="image-preview">
                                <img src="{image_source_escaped}" alt="Imagem enviada para análise" loading="lazy" />
                                <a class="meta-link" href="{image_source_escaped}" target="_blank" rel="noreferrer">{image}</a>
                            </div>
                        </div>
          </div>
          <div class="result">
            <h2>Relatório gerado pela IA</h2>
            {result_html}
          </div>
          <div class="footer">If the link expires, request a new analysis e-mail to receive a refreshed download URL.</div>
        </div>
      </div>
    </div>
  </body>
</html>"""


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _pdf_text(
    x: float,
    y: float,
    text: str,
    font: str = "F1",
    size: int = 11,
    color: tuple[float, float, float] = (0.12, 0.15, 0.2),
) -> str:
    red, green, blue = color
    return (
        "BT\n"
        f"{red:.3f} {green:.3f} {blue:.3f} rg\n"
        f"/{font} {size} Tf\n"
        f"1 0 0 1 {x:.2f} {y:.2f} Tm\n"
        f"({_escape_pdf_text(text)}) Tj\n"
        "ET"
    )


def _pdf_box(
    x: float,
    y: float,
    width: float,
    height: float,
    fill: tuple[float, float, float],
    stroke: tuple[float, float, float] | None = None,
) -> str:
    fill_r, fill_g, fill_b = fill
    if stroke is None:
        stroke_r, stroke_g, stroke_b = fill
    else:
        stroke_r, stroke_g, stroke_b = stroke

    return (
        "q\n"
        f"{fill_r:.3f} {fill_g:.3f} {fill_b:.3f} rg\n"
        f"{stroke_r:.3f} {stroke_g:.3f} {stroke_b:.3f} RG\n"
        f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re\n"
        "B\n"
        "Q"
    )


def _pdf_image(
    x: float, y: float, width: float, height: float, name: str = "Im1"
) -> str:
    return f"q\n{width:.2f} 0 0 {height:.2f} {x:.2f} {y:.2f} cm\n/{name} Do\nQ"


def _wrap_pdf_text(text: str, max_chars: int) -> List[str]:
    wrapped = textwrap.wrap(
        text,
        width=max_chars,
        drop_whitespace=False,
        replace_whitespace=False,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped or [""]


def _write_pdf_object(
    buffer: bytearray, object_number: int, body: bytes, offsets: List[int]
) -> None:
    offsets.append(len(buffer))
    buffer.extend(f"{object_number} 0 obj\n".encode("ascii"))
    buffer.extend(body)
    buffer.extend(b"\nendobj\n")


def _build_pdf_entries(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized = _normalize_dynamodb_value(report)
    result = normalized.get("result", {}) or {}
    technical_analysis = (
        result.get("technical_analysis") if isinstance(result, dict) else result
    )
    entries: List[Dict[str, Any]] = [
        {"kind": "section_title", "text": "Technical Analysis"},
    ]

    technical_lines: List[str] = []
    _build_result_lines(technical_analysis, technical_lines)

    for raw_line in technical_lines:
        stripped_line = raw_line.lstrip()
        indent = (len(raw_line) - len(stripped_line)) // 2
        if stripped_line.endswith(":") and not stripped_line.startswith("- "):
            entries.append(
                {
                    "kind": "section_heading",
                    "text": stripped_line[:-1],
                    "indent": indent,
                }
            )
        elif stripped_line.startswith("- "):
            entries.append(
                {"kind": "bullet", "text": stripped_line[2:], "indent": indent}
            )
        else:
            entries.append({"kind": "text", "text": stripped_line, "indent": indent})

    return entries


def _fit_image_size(
    image_width: int, image_height: int, max_width: float, max_height: float
) -> tuple[float, float]:
    scale = min(max_width / image_width, max_height / image_height, 1.0)
    return image_width * scale, image_height * scale


def _render_pdf_entries(
    entries: Sequence[Dict[str, Any]],
    first_page: bool,
    image_resource: Dict[str, Any] | None = None,
) -> List[bytes]:
    page_width = 612.0
    page_height = 792.0
    body_bottom = 52.0
    body_top_first = 535.0
    body_top_following = 675.0


    pages: List[List[str]] = []
    current_commands: List[str] = []
    current_y = body_top_first if first_page else body_top_following

    def start_page(is_first_page: bool) -> None:
        nonlocal current_commands, current_y
        current_commands = []
        # simple page background
        current_commands.append(
            _pdf_box(
                0, 0, page_width, page_height, (0.97, 0.95, 0.91), (0.97, 0.95, 0.91)
            )
        )
        # set a comfortable top for content
        current_y = 740.0

    def flush_page() -> None:
        pages.append(current_commands.copy())

    def maybe_new_page(is_first_page: bool) -> None:
        start_page(is_first_page)

    def remaining_height() -> float:
        return current_y - body_bottom

    maybe_new_page(first_page)

    for entry_index, entry in enumerate(entries):
        kind = entry["kind"]
        text = str(entry["text"])
        indent = int(entry.get("indent", 0))

        if kind in {"hero_title", "meta_label", "meta_value"}:
            continue

        if kind == "section_title":
            needed_height = 26.0
            if remaining_height() < needed_height:
                flush_page()
                maybe_new_page(False)

            current_commands.append(
                _pdf_text(
                    52, current_y, text, font="F2", size=14, color=(0.06, 0.46, 0.43)
                )
            )
            current_y -= 20.0
            continue

        if kind == "section_heading":
            wrapped = _wrap_pdf_text(text, max(34, 62 - (indent * 4)))
            needed_height = 18.0 * len(wrapped) + 4.0
            if remaining_height() < needed_height:
                flush_page()
                maybe_new_page(False)
                current_commands.append(
                    _pdf_text(
                        52,
                        current_y,
                        "Technical Analysis",
                        font="F2",
                        size=14,
                        color=(0.06, 0.46, 0.43),
                    )
                )
                current_y -= 20.0

            for wrapped_line in wrapped:
                current_commands.append(
                    _pdf_text(
                        56 + indent * 12,
                        current_y,
                        wrapped_line,
                        font="F2",
                        size=11.0,
                        color=(0.08, 0.12, 0.18),
                    )
                )
                current_y -= 16.0
            current_y -= 4.0
            continue

        if kind == "bullet":
            available_chars = max(28, 74 - (indent * 6))
            wrapped = _wrap_pdf_text(text, available_chars)
            needed_height = 14.0 * len(wrapped) + 4.0
            if remaining_height() < needed_height:
                flush_page()
                maybe_new_page(False)
                current_commands.append(
                    _pdf_text(
                        52,
                        current_y,
                        "Technical Analysis",
                        font="F2",
                        size=14,
                        color=(0.06, 0.46, 0.43),
                    )
                )
                current_y -= 20.0

            bullet_x = 56 + indent * 12
            current_commands.append(
                _pdf_text(
                    bullet_x,
                    current_y,
                    f"- {wrapped[0]}",
                    font="F1",
                    size=10.5,
                    color=(0.13, 0.15, 0.21),
                )
            )
            current_y -= 14.0
            for wrapped_line in wrapped[1:]:
                current_commands.append(
                    _pdf_text(
                        bullet_x + 12,
                        current_y,
                        wrapped_line,
                        font="F1",
                        size=10.5,
                        color=(0.13, 0.15, 0.21),
                    )
                )
                current_y -= 14.0
            current_y -= 2.0
            continue

        wrapped = _wrap_pdf_text(text, max(30, 74 - (indent * 6)))
        needed_height = 14.0 * len(wrapped) + 2.0
        if remaining_height() < needed_height:
            flush_page()
            maybe_new_page(False)
            current_commands.append(
                _pdf_text(
                    52,
                    current_y,
                    "Technical Analysis",
                    font="F2",
                    size=14,
                    color=(0.06, 0.46, 0.43),
                )
            )
            current_y -= 20.0

        for wrapped_line in wrapped:
            current_commands.append(
                _pdf_text(
                    56 + indent * 12,
                    current_y,
                    wrapped_line,
                    font="F1",
                    size=10.5,
                    color=(0.13, 0.15, 0.21),
                )
            )
            current_y -= 13.0
        current_y -= 2.0

    flush_page()

    page_bodies: List[bytes] = []
    for commands in pages:
        body = "\n".join(commands).encode("latin-1")
        page_bodies.append(body)

    return page_bodies


def build_pdf_report(report: Dict[str, Any]) -> bytes:
    entries = _build_pdf_entries(report)
    page_bodies = _render_pdf_entries(entries, first_page=True)

    object_count = 4 + len(page_bodies) * 2
    page_object_numbers = [5 + index * 2 for index in range(len(page_bodies))]
    content_object_numbers = [6 + index * 2 for index in range(len(page_bodies))]

    buffer = bytearray(b"%PDF-1.4\n")
    offsets: List[int] = []

    _write_pdf_object(buffer, 1, b"<< /Type /Catalog /Pages 2 0 R >>", offsets)

    kids = " ".join(f"{page_number} 0 R" for page_number in page_object_numbers)
    pages_body = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_bodies)} >>".encode(
        "ascii"
    )
    _write_pdf_object(buffer, 2, pages_body, offsets)

    _write_pdf_object(
        buffer, 3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", offsets
    )
    _write_pdf_object(
        buffer,
        4,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        offsets,
    )

    for page_number, content_number, page_body in zip(
        page_object_numbers, content_object_numbers, page_bodies
    ):
        content_body = (
            b"<< /Length "
            + str(len(page_body)).encode("ascii")
            + b" >>\nstream\n"
            + page_body
            + b"\nendstream"
        )
        _write_pdf_object(buffer, content_number, content_body, offsets)
        page_body_value = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_number} 0 R >>"
        ).encode("ascii")
        _write_pdf_object(buffer, page_number, page_body_value, offsets)

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
