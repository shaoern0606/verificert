import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas


def generate_certificate_pdf(
    recipient_name: str,
    course_name: str,
    certificate_title: str,
    organization_name: str,
    certificate_number: str,
    issue_date: str,
) -> bytes:
    buffer = io.BytesIO()
    width, height = landscape(letter)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    c.setStrokeColor(HexColor("#13795b"))
    c.setLineWidth(3)
    c.rect(24, 24, width - 48, height - 48)

    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#475569"))
    c.drawCentredString(width / 2, height - 100, organization_name)

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(HexColor("#0f172a"))
    c.drawCentredString(width / 2, height - 150, certificate_title)

    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#475569"))
    c.drawCentredString(width / 2, height - 200, "This certifies that")

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(HexColor("#13795b"))
    c.drawCentredString(width / 2, height - 240, recipient_name)

    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#475569"))
    c.drawCentredString(width / 2, height - 275, f"has successfully completed {course_name}")

    c.setFont("Helvetica", 12)
    c.drawString(60, 70, f"Certificate No: {certificate_number}")
    c.drawRightString(width - 60, 70, f"Issued: {issue_date}")

    c.save()
    return buffer.getvalue()
