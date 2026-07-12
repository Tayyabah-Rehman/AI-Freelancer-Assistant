"""
Shared PDF export layer using ReportLab.

Proposal and Cover Letter PDFs are built here today. Day 4's Invoice and
Contract generators will add their own builder functions to this same
file, reusing STYLES so every exported PDF looks consistent.
"""

import io
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle

_BASE_STYLES = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "DocTitle",
    parent=_BASE_STYLES["Title"],
    textColor=colors.HexColor("#1c2321"),
    fontSize=19,
    spaceAfter=4,
)
META_STYLE = ParagraphStyle(
    "DocMeta",
    parent=_BASE_STYLES["Normal"],
    textColor=colors.HexColor("#5a655f"),
    fontSize=9.5,
    spaceAfter=3,
)
BODY_STYLE = ParagraphStyle(
    "DocBody",
    parent=_BASE_STYLES["Normal"],
    fontSize=11,
    leading=16,
    spaceAfter=10,
    textColor=colors.HexColor("#1c2321"),
)


def _esc(value):
    return escape(str(value)) if value else ""


def _build_pdf(title, meta_lines, body_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        title=title,
    )

    story = [Paragraph(_esc(title), TITLE_STYLE)]
    for line in meta_lines:
        story.append(Paragraph(line, META_STYLE))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#3f7a5e"), thickness=1))
    story.append(Spacer(1, 14))

    for paragraph in (body_text or "").split("\n"):
        if paragraph.strip():
            story.append(Paragraph(_esc(paragraph.strip()), BODY_STYLE))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_proposal_pdf(proposal):
    title = f"Proposal - {proposal.project_title or 'Untitled Project'}"
    meta_lines = [
        f"Prepared for: {_esc(proposal.client_name) or 'N/A'}",
        f"Budget: {_esc(proposal.budget) or 'Not specified'}  |  Timeline: {_esc(proposal.timeline) or 'Not specified'}",
        f"Generated on {proposal.created_at.strftime('%B %d, %Y')}",
    ]
    return _build_pdf(title, meta_lines, proposal.generated_content)


def generate_cover_letter_pdf(letter):
    title = f"Cover Letter - {letter.job_title or 'Untitled Role'}"
    meta_lines = [
        f"Applying to: {_esc(letter.company_name) or 'N/A'}",
        f"Generated on {letter.created_at.strftime('%B %d, %Y')}",
    ]
    return _build_pdf(title, meta_lines, letter.generated_content)


def generate_invoice_pdf(invoice):
    tax_amount = round((invoice.amount or 0) * (invoice.tax or 0) / 100, 2)
    total = round((invoice.amount or 0) + tax_amount, 2)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        title=f"Invoice {invoice.invoice_number or ''}",
    )

    story = [Paragraph(_esc(f"Invoice {invoice.invoice_number or ''}"), TITLE_STYLE)]

    bill_to = f"Bill To: {_esc(invoice.client_name) or 'N/A'}"
    if invoice.client_email:
        bill_to += f" ({_esc(invoice.client_email)})"
    story.append(Paragraph(bill_to, META_STYLE))
    story.append(Paragraph(f"Date Issued: {invoice.created_at.strftime('%B %d, %Y')}", META_STYLE))
    if invoice.due_date:
        story.append(Paragraph(f"Due Date: {invoice.due_date.strftime('%B %d, %Y')}", META_STYLE))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#3f7a5e"), thickness=1))
    story.append(Spacer(1, 14))

    if invoice.project_details:
        story.append(Paragraph(f"<b>Project:</b> {_esc(invoice.project_details)}", BODY_STYLE))
        story.append(Spacer(1, 10))

    table_data = [
        ["Description", "Amount"],
        [_esc(invoice.services) or "Services rendered", f"${invoice.amount:,.2f}"],
        ["Subtotal", f"${invoice.amount:,.2f}"],
        [f"Tax ({invoice.tax or 0:g}%)", f"${tax_amount:,.2f}"],
        ["Total Due", f"${total:,.2f}"],
    ]
    table = Table(table_data, colWidths=[3.9 * inch, 1.7 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3f7a5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#414d48")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8ece9")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_contract_pdf(contract):
    title = f"Service Agreement - {contract.client_name or 'Untitled'}"
    meta_lines = [
        f"Between: {_esc(contract.freelancer_name) or 'Freelancer'} and {_esc(contract.client_name) or 'Client'}",
        f"Timeline: {_esc(contract.timeline) or 'Not specified'}",
        f"Generated on {contract.created_at.strftime('%B %d, %Y')}",
    ]
    return _build_pdf(title, meta_lines, contract.generated_content)
