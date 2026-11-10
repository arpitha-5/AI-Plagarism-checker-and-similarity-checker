from __future__ import annotations

import html
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .plagiarism.text_preprocessor import split_sentences


PAGE_W, PAGE_H = A4
INK = colors.HexColor("#171717")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#D7DCE2")
BLUE = colors.HexColor("#2563EB")
GREEN = colors.HexColor("#16A34A")
RED = colors.HexColor("#DC2626")
ORANGE = colors.HexColor("#F59E0B")
SOURCE_COLORS = [
    colors.HexColor("#7C3AED"),
    colors.HexColor("#DB2777"),
    colors.HexColor("#0891B2"),
    colors.HexColor("#65A30D"),
    colors.HexColor("#EA580C"),
    colors.HexColor("#2563EB"),
]


def _value(value: Any, fallback: str = "Not available") -> str:
    return fallback if value is None or value == "" else str(value)


def _safe(value: Any, fallback: str = "Not available") -> str:
    return html.escape(_value(value, fallback))


def _group_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: list[dict[str, Any]] = []
    for match in sorted(matches, key=lambda item: item.get("candidate_sentence_position", 0)):
        if (
            grouped
            and grouped[-1].get("match_type") == match.get("match_type")
            and match.get("candidate_sentence_position", 0)
            == grouped[-1].get("candidate_end", -2) + 1
        ):
            grouped[-1]["candidate_end"] = match.get("candidate_sentence_position")
            grouped[-1]["source_end"] = match.get("source_sentence_position")
            grouped[-1]["text"] += " " + match.get("text", "")
            grouped[-1]["source_text"] = (
                grouped[-1].get("source_text", "")
                + " "
                + match.get("source_text", match.get("text", ""))
            )
        else:
            grouped.append({
                **match,
                "candidate_end": match.get("candidate_sentence_position"),
                "source_end": match.get("source_sentence_position"),
            })
    return grouped


def _footer(canvas: Any, document: Any) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 8.5 * mm, "PlagiarismAI  |  Similarity report")
    canvas.drawRightString(192 * mm, 8.5 * mm, f"Page {document.page}")
    canvas.restoreState()


def _header(canvas: Any, document: Any) -> None:
    _footer(canvas, document)
    if document.page > 1:
        canvas.saveState()
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(
            192 * mm,
            PAGE_H - 10 * mm,
            f"Page {document.page} of report  |  Submission ID {_value(getattr(document, 'submission_id', None), '—')}",
        )
        canvas.restoreState()


def _table(data: list[list[Any]], widths: list[float], header: bool = True) -> Table:
    style = [
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
    ]
    if header:
        style.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    table.setStyle(TableStyle(style))
    return table


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover": ParagraphStyle("cover", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=INK),
        "heading": ParagraphStyle("heading", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=INK, spaceAfter=8),
        "subheading": ParagraphStyle("subheading", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=INK, spaceBefore=5, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=INK, spaceAfter=5),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.4, leading=9.5, textColor=INK, spaceAfter=2),
        "tiny": ParagraphStyle("tiny", parent=base["BodyText"], fontName="Helvetica", fontSize=6.8, leading=8.3, textColor=INK),
        "metric": ParagraphStyle("metric", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=24, leading=27, textColor=INK),
        "column": ParagraphStyle("column", parent=base["BodyText"], fontName="Helvetica", fontSize=7.25, leading=9.2, textColor=INK, alignment=TA_LEFT, spaceAfter=3),
        "column_match": ParagraphStyle("column_match", parent=base["BodyText"], fontName="Helvetica", fontSize=7.25, leading=9.2, textColor=INK, backColor=colors.HexColor("#FFF1F2"), spaceAfter=3, borderPadding=2),
    }


def _source_data(analysis: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    sources = analysis.get("source_documents", [])
    exact: list[dict[str, Any]] = []
    near: list[dict[str, Any]] = []
    for source_index, source in enumerate(sources):
        for match in source.get("exact_matches", []):
            exact.append({**match, "_source_index": source_index})
        for match in source.get("near_duplicate_matches", []):
            near.append({**match, "_source_index": source_index})
    return sources, exact, near


def _document_flowables(
    text: str,
    exact: list[dict[str, Any]],
    near: list[dict[str, Any]],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    all_sentences = split_sentences(text)
    match_by_position: dict[int, dict[str, Any]] = {}
    for match in exact + near:
        position = match.get("candidate_sentence_position")
        if position is not None and position not in match_by_position:
            match_by_position[position] = match
    flowables: list[Any] = []
    for position, sentence in enumerate(all_sentences):
        match = match_by_position.get(position)
        if match:
            source_number = int(match.get("_source_index", 0)) + 1
            match_style = ParagraphStyle(
                f"match_{position}",
                parent=styles["column_match"],
                backColor=colors.HexColor("#FFF7ED") if match.get("match_type") == "near_duplicate" else colors.HexColor("#FEF2F2"),
                borderColor=SOURCE_COLORS[(source_number - 1) % len(SOURCE_COLORS)],
                borderWidth=1.5,
                borderPadding=2,
            )
            content = f"<font color='{SOURCE_COLORS[(source_number - 1) % len(SOURCE_COLORS)].hexval()}'><b>[{source_number}]</b></font> {_safe(sentence)}"
            flowables.append(Paragraph(content, match_style))
        else:
            flowables.append(Paragraph(_safe(sentence), styles["column"]))
    return flowables


def _pdf_page_flowables(
    source_path: Path,
    exact: list[dict[str, Any]],
    near: list[dict[str, Any]],
) -> list[Any]:
    try:
        import fitz
    except ModuleNotFoundError as error:
        raise RuntimeError("PDF page rendering requires PyMuPDF.") from error

    matches = exact + near
    document = fitz.open(source_path)
    flowables: list[Any] = []
    for page in document:
        for match in matches:
            candidate_text = str(match.get("text", "")).strip()
            if not candidate_text:
                continue
            source_number = int(match.get("_source_index", 0)) + 1
            colour = SOURCE_COLORS[(source_number - 1) % len(SOURCE_COLORS)]
            pdf_colour = (colour.red, colour.green, colour.blue)
            rectangles = page.search_for(candidate_text)
            for rectangle in rectangles:
                page.draw_rect(
                    rectangle,
                    color=pdf_colour,
                    fill=pdf_colour,
                    fill_opacity=0.18,
                    width=1.2,
                )
                page.insert_text(
                    (rectangle.x0, max(8, rectangle.y0 - 1)),
                    str(source_number),
                    fontsize=6,
                    color=pdf_colour,
                )
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.45, 1.45), alpha=False)
        image = Image(
            io.BytesIO(pixmap.tobytes("png")),
            width=174 * mm,
            height=255 * mm,
            hAlign="CENTER",
        )
        flowables.append(image)
        if page.number < len(document) - 1:
            flowables.append(PageBreak())
    document.close()
    return flowables


def generate_report(
    output_path: Path,
    analysis: dict[str, Any],
    document_text: str,
    generated_at: datetime,
    source_path: Path | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    metadata = analysis.get("document_metadata", {})
    sources, exact_matches, near_matches = _source_data(analysis)
    all_matches = _group_matches(exact_matches + near_matches)
    categories = analysis.get("source_categories", {})
    groups = analysis.get("match_groups", {})
    filters = analysis.get("filters", {})
    document_name = _value(analysis.get("document_name"), "Text analysis")
    submission_id = _value(analysis.get("id"), "Not available")
    source_count = len(sources)
    unique_match_count = len({m.get("candidate_sentence_position") for m in exact_matches + near_matches})
    document_pages = metadata.get("page_count")
    company = _value(metadata.get("institution_name"), "Institute of Aeronautical Engineering (IARE)")

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title="PlagiarismAI similarity report",
        author="PlagiarismAI",
    )
    doc.submission_id = submission_id
    single = Frame(18 * mm, 20 * mm, 174 * mm, 255 * mm, id="single", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    columns = [
        Frame(18 * mm, 20 * mm, 82 * mm, 255 * mm, id="left", leftPadding=0, rightPadding=4 * mm, topPadding=0, bottomPadding=0),
        Frame(110 * mm, 20 * mm, 82 * mm, 255 * mm, id="right", leftPadding=4 * mm, rightPadding=0, topPadding=0, bottomPadding=0),
    ]
    doc.addPageTemplates([
        PageTemplate(id="single", frames=single, onPage=_header),
        PageTemplate(id="columns", frames=columns, onPage=_header),
    ])

    story: list[Any] = [
        Spacer(1, 55 * mm),
        Paragraph("PlagiarismAI", ParagraphStyle("brand", parent=styles["cover"], fontSize=23, leading=27, textColor=BLUE)),
        Spacer(1, 8 * mm),
        Paragraph(_safe(document_name), styles["cover"]),
        Spacer(1, 4 * mm),
        Paragraph("Document similarity report", styles["body"]),
        Spacer(1, 23 * mm),
        Paragraph("Document Details", styles["subheading"]),
    ]
    cover_rows = [
        ["Reference identification", company],
        ["Submission ID", submission_id],
        ["Submission date", _value(analysis.get("created_at"))],
        ["Report generated", generated_at.isoformat(timespec="seconds")],
        ["File Name", document_name],
        ["File Size", f"{metadata['file_size_bytes']:,} bytes" if metadata.get("file_size_bytes") else "Not available"],
        ["Pages", _value(document_pages, "Not available")],
        ["Words", f"{metadata.get('word_count', 0):,}"],
        ["Characters", f"{metadata.get('character_count', len(document_text)):,}"],
    ]
    story.append(_table(cover_rows, [48 * mm, 112 * mm], header=False))
    story.append(PageBreak())

    similarity = _value(analysis.get("similarity_percentage"), "—")
    overview_title = Paragraph("Integrity Overview", styles["heading"])
    story.extend([
        overview_title,
        Paragraph(f"<font size='24'><b>{_safe(similarity)}%</b></font>  <b>Overall Similarity</b>", styles["metric"]),
        Paragraph("The combined total of valid unique matches in the authorized source corpus. Direct and near-duplicate matches are calculated separately; semantic similarity is not added to this percentage.", styles["body"]),
        Spacer(1, 4 * mm),
        Paragraph("Filtered from the Report", styles["subheading"]),
    ])
    filter_rows = [["Bibliography", "Quoted Text", "Cited Text", "Small Matches"]]
    filter_rows.append([
        "Applied" if filters.get("bibliography") else "Not applied",
        "Applied" if filters.get("quoted_text") else "Not applied",
        "Applied" if filters.get("cited_text") else "Not applied",
        "Applied" if filters.get("small_matches") else "Not applied",
    ])
    story.append(_table(filter_rows, [43.5 * mm] * 4))
    story.extend([
        Spacer(1, 7 * mm),
        Paragraph("Match Groups", styles["subheading"]),
        _table([
            ["Group", "Matches", "Percentage"],
            ["Not Cited or Quoted", _value(groups.get("not_cited_or_quoted"), "Unavailable"), _safe(similarity) + "%"],
            ["Missing Quotations", _value(groups.get("missing_quotations"), "Unavailable"), "Unavailable"],
            ["Missing Citation", _value(groups.get("missing_citation"), "Unavailable"), "Unavailable"],
            ["Cited and Quoted", _value(groups.get("cited_and_quoted"), "Unavailable"), "Unavailable"],
        ], [88 * mm, 43 * mm, 43 * mm]),
        Spacer(1, 7 * mm),
        Paragraph("Top Sources", styles["subheading"]),
        _table([
            ["Category", "Sources", "Contribution"],
            ["Internet sources", str(len(categories.get("internet_sources", []))), "Unavailable" if not categories.get("internet_sources") else "Calculated"],
            ["Publications", str(len(categories.get("publications", []))), "Unavailable" if not categories.get("publications") else "Calculated"],
            ["Submitted works", str(len(categories.get("submitted_works", []))), "Unavailable" if not categories.get("submitted_works") else "Calculated"],
            ["Uploaded documents", str(len(categories.get("uploaded_documents", []))), "Calculated" if categories.get("uploaded_documents") else "No matches"],
        ], [73 * mm, 40 * mm, 61 * mm]),
        Spacer(1, 7 * mm),
        Paragraph("Integrity Flags", styles["subheading"]),
        Paragraph(
            "No suspicious text manipulations found." if not analysis.get("integrity_flags") else f"{len(analysis['integrity_flags'])} evidence-based flag(s) require review.",
            styles["body"],
        ),
        PageBreak(),
    ])

    source_rows = [["#", "Source", "Type", "Match"]]
    for index, source in enumerate(sources, 1):
        positions = {
            m.get("candidate_sentence_position")
            for m in source.get("exact_matches", []) + source.get("near_duplicate_matches", [])
        }
        contribution = (len(positions) / max(unique_match_count, 1)) * 100
        source_rows.append([
            str(index),
            _value(source.get("source_document_name"), "Uploaded document"),
            "Uploaded document",
            f"{contribution:.2f}%",
        ])
    story.extend([
        Paragraph("Integrity Overview", styles["heading"]),
        Paragraph("Top Sources", styles["subheading"]),
        Paragraph("The sources with the highest number of meaningful matches within the submission. Duplicate content hashes are represented once.", styles["body"]),
        _table(source_rows, [12 * mm, 92 * mm, 36 * mm, 34 * mm]) if sources else Paragraph("No matching sources were returned from the available authorized corpus.", styles["body"]),
        Spacer(1, 8 * mm),
        Paragraph("Source Coverage", styles["subheading"]),
        _table([
            ["Category", "Availability", "Count"],
            ["Internet sources", "Configured" if categories.get("internet_sources") else "Unavailable", str(len(categories.get("internet_sources", [])))],
            ["Publications", "Configured" if categories.get("publications") else "Unavailable", str(len(categories.get("publications", [])))],
            ["Submitted works", "Configured" if categories.get("submitted_works") else "Unavailable", str(len(categories.get("submitted_works", [])))],
            ["Uploaded documents", "Configured" if categories.get("uploaded_documents") else "No matches", str(len(categories.get("uploaded_documents", [])))],
        ], [62 * mm, 88 * mm, 24 * mm]),
        Spacer(1, 8 * mm),
        Paragraph("Matching Summary", styles["subheading"]),
        Paragraph(f"{source_count} unique source(s), {len(exact_matches)} direct match(es), {len(near_matches)} near-duplicate match(es), and {len(all_matches)} grouped passage block(s).", styles["body"]),
        Paragraph("Source colours used in the document view:", styles["body"]),
    ])
    legend = [["Source", "Colour", "Match type"]]
    for index, source in enumerate(sources, 1):
        legend.append([str(index), "", "Direct and near-duplicate passages"])
    legend_table = _table(legend, [25 * mm, 25 * mm, 110 * mm])
    legend_table.setStyle(TableStyle([
        ("BACKGROUND", (1, 1), (1, -1), SOURCE_COLORS[0] if sources else colors.white),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.white),
    ]))
    source_is_pdf = bool(
        source_path
        and source_path.is_file()
        and source_path.suffix.casefold() == ".pdf"
    )
    story.extend([
        legend_table,
        NextPageTemplate("single" if source_is_pdf else "columns"),
        PageBreak(),
    ])
    if source_is_pdf:
        story.extend(_pdf_page_flowables(source_path, exact_matches, near_matches))
    else:
        story.append(Paragraph(f"{_safe(document_name)}  |  Analysed document", styles["subheading"]))
        story.append(Paragraph("Rendered from the original uploaded document text. Matching passages are marked with numbered source indicators.", styles["body"]))
        story.extend(_document_flowables(document_text, exact_matches, near_matches, styles))
    story.extend([
        NextPageTemplate("single"),
        PageBreak(),
        Paragraph("Detailed Matching", styles["heading"]),
        Paragraph("Matching passages are shown in the analysed-document pages using the numbered source markers. The table below preserves the corresponding source passage and match type.", styles["body"]),
    ])
    if all_matches:
        detail_rows = [["#", "Source", "Type", "Submitted passage", "Source passage"]]
        for index, match in enumerate(all_matches, 1):
            detail_rows.append([
                str(index),
                str(int(match.get("_source_index", 0)) + 1),
                "Direct" if match.get("match_type") == "exact" else "Near duplicate",
                Paragraph(_safe(match.get("text")), styles["tiny"]),
                Paragraph(_safe(match.get("source_text", match.get("text"))), styles["tiny"]),
            ])
        story.append(_table(detail_rows, [10 * mm, 15 * mm, 28 * mm, 60 * mm, 61 * mm]))
    else:
        story.append(Paragraph("No matching passages were found in the authorized source corpus.", styles["body"]))
    story.extend([
        PageBreak(),
        Paragraph("Integrity Observations", styles["heading"]),
        Paragraph("Flags are evidence for review, not findings of misconduct.", styles["body"]),
    ])
    if analysis.get("integrity_flags"):
        flag_rows = [["Category", "Severity", "Location", "Evidence"]]
        for flag in analysis["integrity_flags"]:
            flag_rows.append([
                _value(flag.get("category")),
                _value(flag.get("severity")),
                _value(flag.get("location")),
                _value(flag.get("evidence")),
            ])
        story.append(_table(flag_rows, [38 * mm, 25 * mm, 38 * mm, 73 * mm]))
    else:
        story.append(Paragraph("No evidence-based integrity flags were detected by the configured checks.", styles["body"]))
    story.extend([
        Spacer(1, 8 * mm),
        Paragraph("Methodology and Limitations", styles["heading"]),
        Paragraph(_safe(analysis.get("processing", {}).get("calculation_methodology"), "Methodology unavailable."), styles["body"]),
        Paragraph("Source coverage is limited to the authorized uploaded-document corpus. Internet sources and indexed publications are unavailable unless configured. A similarity score is a review signal and is not, by itself, a conclusion of plagiarism. No-match results do not certify originality.", styles["body"]),
    ])
    doc.build(story)
