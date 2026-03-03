from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import datetime
import io


def generate_lab_pdf(filename, observations, clinical_summary):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)

    width, height = LETTER
    y = height - 50

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "AI-Powered Lab Report")
    y -= 30

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Source File: {filename}")
    y -= 15
    pdf.drawString(50, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30

    # Clinical Summary
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Clinical Summary")
    y -= 20

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, clinical_summary)
    y -= 30

    # Table Header
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Test")
    pdf.drawString(110, y, "Value")
    pdf.drawString(170, y, "Units")
    pdf.drawString(240, y, "Reference")
    pdf.drawString(330, y, "Flag")
    pdf.drawString(380, y, "LOINC")
    y -= 15

    pdf.line(50, y, 550, y)
    y -= 10

    # Table Rows
    pdf.setFont("Helvetica", 10)
    for obs in observations:
        pdf.drawString(50, y, obs["test"])
        pdf.drawString(110, y, str(obs["value"]))
        pdf.drawString(170, y, obs["units"])
        pdf.drawString(240, y, obs["reference_range"])
        pdf.drawString(330, y, obs["flag"])
        pdf.drawString(380, y, obs.get("loinc", ""))
        y -= 15

        if y < 50:
            pdf.showPage()
            y = height - 50

    # Footer
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer
