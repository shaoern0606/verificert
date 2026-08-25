import io

import qrcode
from pypdf import PdfReader, PdfWriter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def stamp_pdf_with_qr(pdf_bytes: bytes, verification_url: str) -> bytes:
    qr_buffer = io.BytesIO()
    qrcode.make(verification_url).save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    qr_size = 1.1 * inch
    margin = 0.35 * inch
    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
    c.drawImage(
        ImageReader(qr_buffer),
        page_width - qr_size - margin,
        margin,
        width=qr_size,
        height=qr_size,
        mask="auto",
    )
    c.setFont("Helvetica", 6)
    c.drawRightString(page_width - margin, margin - 8, "Scan to verify")
    c.save()
    overlay_buffer.seek(0)

    overlay_reader = PdfReader(overlay_buffer)
    first_page.merge_page(overlay_reader.pages[0])

    writer = PdfWriter()
    writer.add_page(first_page)
    for page in reader.pages[1:]:
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
