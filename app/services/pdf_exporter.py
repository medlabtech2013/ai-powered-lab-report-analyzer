from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch


def generate_lab_report_pdf(filename, patient_name, dob, mrn, summary, observations):
    doc = SimpleDocTemplate(filename, pagesize=pagesizes.letter)
    elements = []

    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]
    normal_style = styles["Normal"]

    # Title
    elements.append(Paragraph("CliniSight AI™ Clinical Intelligence Platform", title_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Patient Info
    elements.append(Paragraph(f"<b>Patient:</b> {patient_name}", normal_style))
    elements.append(Paragraph(f"<b>DOB:</b> {dob}", normal_style))
    elements.append(Paragraph(f"<b>MRN:</b> {mrn}", normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Insight / Summary Section
    insight_style = ParagraphStyle(
        "InsightStyle",
        parent=styles["Normal"],
        backColor=colors.lightblue,
        borderWidth=1,
        borderColor=colors.blue,
        borderPadding=6,
        spaceAfter=10
    )

    elements.append(Paragraph("<b>Clinical Insight</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(summary or "No summary available.", insight_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Table Header
    table_data = [
        ["Test", "Value", "Units", "Reference", "Flag", "LOINC"]
    ]

    for obs in observations:
        table_data.append([
            obs.get("test", ""),
            str(obs.get("value", "")),
            obs.get("units", ""),
            obs.get("reference", ""),
            obs.get("flag", ""),
            obs.get("loinc", "")
        ])

    table = Table(table_data, repeatRows=1)

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ])

    # Apply row coloring
    for i, obs in enumerate(observations, start=1):
        flag = obs.get("flag")
        if flag == "H":
            style.add("BACKGROUND", (0, i), (-1, i), colors.Color(1, 0.85, 0.85))
        elif flag == "L":
            style.add("BACKGROUND", (0, i), (-1, i), colors.Color(0.85, 0.92, 1))

    table.setStyle(style)

    elements.append(table)

    doc.build(elements)

    return filename
