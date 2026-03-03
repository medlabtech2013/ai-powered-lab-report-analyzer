from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

from parser import parse_hl7  

from datetime import datetime
from fastapi.responses import HTMLResponse
import hashlib
import base64
from io import BytesIO
import math
import sqlite3
import json
import os

app = FastAPI()

# -------------------------
# GLOBAL STORAGE
# -------------------------
LAB_HISTORY = []
LAST_RESULT = None

DB_PATH = os.getenv("DB_PATH", "data/reports.db")

if not os.getenv("DB_PATH"):
    os.makedirs("data", exist_ok=True)

APP_NAME = "CliniSight AI™ Clinical Intelligence Platform"
REPORT_NAME = "CliniSight AI™ Clinical Intelligence Report"
MODEL_NAME = "CliniSight Risk Engine"
MODEL_VERSION = "v1.0.0"   # bump this when logic changes

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            report_hash TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            encounter_id TEXT NOT NULL,
            patient_name TEXT,
            dob TEXT,
            mrn TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()



# Report registry for verification
REPORT_REGISTRY = {}  # report_id -> {"hash": str, "result": dict, "generated_at": str}

def save_report_to_db(report_id: str, report_hash: str, generated_at: str, snapshot: dict,
                      model_name: str, model_version: str, encounter_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO reports (
            report_id, report_hash, generated_at, snapshot_json,
            model_name, model_version, encounter_id,
            patient_name, dob, mrn
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id.upper(),
        report_hash,
        generated_at,
        json.dumps(snapshot),
        model_name,
        model_version,
        encounter_id,
        snapshot.get("patientName"),
        snapshot.get("dob"),
        snapshot.get("mrn")
    ))
    conn.commit()
    conn.close()

def get_report_from_db(report_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT report_id, report_hash, generated_at, snapshot_json,
               model_name, model_version, encounter_id,
               patient_name, dob, mrn
        FROM reports
        WHERE report_id = ?
    """, (report_id.upper(),))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None

    return {
        "report_id": row[0],
        "hash": row[1],
        "generated_at": row[2],
        "snapshot": json.loads(row[3]),
        "model_name": row[4],
        "model_version": row[5],
        "encounter_id": row[6],
        "patient_name": row[7],
        "dob": row[8],
        "mrn": row[9],
    }

# -------------------------
# MIDDLEWARE
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# -------------------------
# UI
# -------------------------
@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    with open("frontend/index.html", "r") as f:
        return f.read()

# -------------------------
# RISK CALCULATION
# -------------------------
def calculate_risk_backend(observations):
    risk_score = 0

    for obs in observations:
        test = obs.get("test", "").upper()
        value = float(obs.get("value", 0))

        if test == "WBC" and value > 20:
            risk_score += 2
        elif test == "WBC" and value > 11:
            risk_score += 1

        if test == "HGB" and value < 7:
            risk_score += 2
        elif test == "HGB" and value < 12:
            risk_score += 1

    if risk_score >= 3:
        risk_level = "HIGH"
    elif risk_score == 2:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return risk_score, risk_level

# -------------------------
# ANALYZE
# -------------------------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = await file.read()
    content = content.decode("utf-8")

    parsed = parse_hl7(content)
    observations = parsed["observations"]

    summary = parsed.get("summary", "No summary available.")

    risk_score, risk_level = calculate_risk_backend(observations)

    deterioration_index = min(risk_score * 25, 100)
    probability_percent = min(risk_score * 20, 100)

    result = {
        "summary": summary,
        "observations": observations,
        "riskScore": risk_score,
        "riskLevel": risk_level,
        "deteriorationIndex": deterioration_index,
        "probabilityPercent": probability_percent,
        "patientName": parsed.get("patientName", "Anonymous"),
        "dob": parsed.get("dob", "—"),
        "mrn": parsed.get("mrn", "—")
    }

    global LAST_RESULT
    LAST_RESULT = result

    LAB_HISTORY.append(result)

    return result

# -------------------------
# TRENDS
# -------------------------
@app.get("/trends")
def get_trends():
    trend_data = {}

    for run in LAB_HISTORY:
        for obs in run.get("observations", []):
            test = obs.get("test")
            value = obs.get("value")

            try:
                value = float(value)
            except:
                continue

            if test not in trend_data:
                trend_data[test] = []

            trend_data[test].append(value)

    return trend_data

# -------------------------
# DOWNLOAD PDF
# -------------------------
from fastapi import Request
from reportlab.platypus import Image
import base64

from reportlab.pdfgen import canvas

def add_page_number(canvas_obj, doc):
    page_num_text = f"Page {doc.page}"
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawRightString(800, 20, page_num_text)

def add_page_decorations(canvas_obj, doc):
    add_page_number(canvas_obj, doc)
    add_watermark(canvas_obj, doc)

@app.post("/download/pdf")
async def download_pdf(request: Request):
    global LAST_RESULT, REPORT_REGISTRY

    if not LAST_RESULT:
        return JSONResponse({"detail": "No analysis available"}, status_code=400)

    from reportlab.lib.pagesizes import landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing
    import math

    # -------------------------
    # RECEIVE CHART IMAGE
    # -------------------------
    data = await request.json()
    chart_image = data.get("chartImage")
    chart_path = None

    if chart_image:
        header, encoded = chart_image.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        chart_path = "trend_chart.png"
        with open(chart_path, "wb") as f:
            f.write(image_bytes)
    
    # -------------------------
    # CREATE SIGNATURE
    # -------------------------
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_signature_source = str(LAST_RESULT) + generated_at + MODEL_VERSION
    report_hash = hashlib.sha256(report_signature_source.encode()).hexdigest()

    report_id = hashlib.md5(generated_at.encode()).hexdigest()[:8].upper()

    encounter_id = hashlib.md5(
        (str(LAST_RESULT) + generated_at).encode()
    ).hexdigest()[:12].upper()

    # Save to DB (single correct call)
    save_report_to_db(
        report_id,
        report_hash,
        generated_at,
        LAST_RESULT,
        MODEL_NAME,
        MODEL_VERSION,
        encounter_id
    )

    REPORT_REGISTRY[report_id] = {
        "hash": report_hash,
        "result": LAST_RESULT,
        "generated_at": generated_at
    }

    # -------------------------
    # BUILD PDF
    # -------------------------
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []

    # -------------------------
    # HEADER
    # -------------------------
    logo_path = "static/assets/hospital_logo.png"
    badge_path = "static/assets/accreditation_badge.png"

    hospital_style = ParagraphStyle(
        name="HospitalStyle",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#003366"),
        alignment=TA_LEFT
    )

    hospital_title = Paragraph(
        "<b>PrecisionPoint Medical Center</b><br/>"
        "<font size=9 color='#8A8D91'>Clinical Data. Intelligent Care.</font><br/><br/>"
        "<b>Powered by CliniSight AI™</b><br/>"
        "<font size=9 color='#8A8D91'>Where Clinical Data Becomes Intelligence.</font><br/>"
        "<font size=8 color='#8A8D91'>v1.0 Clinical Intelligence Engine</font>",
        hospital_style
    )

    logo = ""
    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo._restrictSize(1.5 * inch, 0.8 * inch)

    badge = ""
    if os.path.exists(badge_path):
        badge = Image(badge_path)
        badge._restrictSize(0.9 * inch, 0.9 * inch)

    header_table = Table([[logo, hospital_title, badge]],
                         colWidths=[130, 520, 80])

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        "CliniSight AI™ Clinical Intelligence Report",
        styles["Heading1"]
    ))
    elements.append(Spacer(1, 12))

    # -------------------------
    # EXECUTIVE SUMMARY
    # -------------------------
    risk_level = LAST_RESULT.get("riskLevel", "—")
    risk_score = LAST_RESULT.get("riskScore", 0)
    probability = LAST_RESULT.get("probabilityPercent", 0)

    elements.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    exec_table = Table([
        ["Report ID", report_id, "Generated", generated_at],
        ["Encounter ID", encounter_id, "Risk Level", risk_level],
        ["Patient", LAST_RESULT.get("patientName", "—"), "DOB", LAST_RESULT.get("dob", "—")],
        ["MRN", LAST_RESULT.get("mrn", "—"), "Risk Score", str(risk_score)],
        ["Predicted Probability", f"{probability}%", "Model Version", MODEL_VERSION],
    ], colWidths=[130, 220, 130, 220])

    exec_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(exec_table)
    elements.append(Spacer(1, 12))

    # -------------------------
    # RISK BANNER
    # -------------------------
    banner_color = colors.green
    if risk_level == "MODERATE":
        banner_color = colors.orange
    elif risk_level == "HIGH":
        banner_color = colors.red

    banner = Table([[f"RISK STATUS: {risk_level}"]],
                   colWidths=[730])

    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), banner_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
    ]))

    elements.append(banner)
    elements.append(Spacer(1, 12))

    # -------------------------
    # CONFIDENCE INTERVAL
    # -------------------------
    n = max(len(LAST_RESULT.get("observations", [])), 1)
    p = max(min(probability / 100.0, 1.0), 0.0)
    se = math.sqrt((p * (1 - p)) / (n + 10))
    low = max(0.0, (p - 1.96 * se) * 100)
    high = min(100.0, (p + 1.96 * se) * 100)

    elements.append(Paragraph(
        f"<b>Model Confidence (95% CI):</b> {low:.1f}% – {high:.1f}%",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    # -------------------------
    # HASH + QR
    # -------------------------
    BASE_URL = request.base_url._url.rstrip("/")
    verify_url = f"{BASE_URL}/verify/{report_id}"

    elements.append(Paragraph(report_hash, styles["Normal"]))
    elements.append(Spacer(1, 8))

    from reportlab.platypus import PageBreak
    elements.append(PageBreak())

    # -------------------------
    # PAGE 2 — DETAILED CLINICAL DATA
    # -------------------------

    elements.append(Paragraph("<b>Detailed Laboratory Observations</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    table_data = [["Test", "Value", "Units", "Reference", "Flag"]]

    for obs in LAST_RESULT["observations"]:
        table_data.append([
            obs.get("test", ""),
            str(obs.get("value", "")),
            obs.get("units", ""),
            obs.get("reference_range", ""),
            obs.get("flag", "")
        ])

    obs_table = Table(table_data, repeatRows=1,
                      colWidths=[120, 80, 100, 160, 80])

    obs_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b64")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(obs_table)
    elements.append(Spacer(1, 20))

    if chart_path:
        elements.append(Paragraph("<b>Trend Visualization</b>", styles["Heading2"]))
        elements.append(Spacer(1, 8))

        trend_img = Image(chart_path, width=500, height=250)
        elements.append(trend_img)
        elements.append(Spacer(1, 20))

    drivers = get_rule_drivers(LAST_RESULT.get("observations", []))

    elements.append(Paragraph("<b>Feature Importance / Drivers</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    if not drivers:
        elements.append(Paragraph("No contributing drivers identified.", styles["Normal"]))
    else:
        driver_table_data = [["Driver", "Contribution (pts)"]]

        for name, pts in drivers:
            driver_table_data.append([name, str(pts)])

        driver_table = Table(driver_table_data, colWidths=[450, 150])

        driver_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b64")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))

        elements.append(driver_table)

    elements.append(Spacer(1, 12))

    # -------------------------
    # MODEL PERFORMANCE METRICS
    # -------------------------
    elements.append(Paragraph("<b>Model Performance Metrics</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    model_table = Table([
        ["Model Name", "CliniSight Risk Engine"],
        ["Version", "v1.0 Clinical Intelligence Engine"],
        ["Risk Logic", "Rule-based (WBC/HGB thresholds)"],
        ["Confidence Method", "Heuristic 95% CI"],
        ["FHIR Compatible", "Yes"],
        ["LOINC Compatible", "Yes"],
        ["Validation Status", "Prototype — Clinical Review Recommended"]
    ], colWidths=[200, 400])

    model_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(model_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Digital Authenticity Signature (SHA256)</b>",
                              styles["Normal"]))
    elements.append(Paragraph(report_hash, styles["Normal"]))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(f"Verify: {verify_url}", styles["Normal"]))
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing

    qr_code = qr.QrCodeWidget(verify_url)
    bounds = qr_code.getBounds()
    size = 90
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]

    d = Drawing(size, size,
                transform=[size / w, 0, 0, size / h, 0, 0])
    d.add(qr_code)    

    elements.append(d)

    # -------------------------
    # BUILD
    # -------------------------
    doc.build(elements,
              onFirstPage=add_page_decorations,
              onLaterPages=add_page_decorations)

    buffer.seek(0)

    if chart_path and os.path.exists(chart_path):
        os.remove(chart_path)

    return StreamingResponse(
    buffer,
    media_type="application/pdf",
    headers={
        "Content-Disposition":
        f"attachment; filename=CliniSight_AI_Report_{report_id}.pdf"
    }
)

@app.get("/verify/{report_id}", response_class=HTMLResponse)
def verify_report(report_id: str):

    record = get_report_from_db(report_id)

    if not record:
        return f"""
        <html>
        <head>
            <title>Report Verification</title>
            <style>
                body {{ font-family: Arial; background: #eef2f7; padding: 50px; }}
                .card {{ background: white; padding: 40px; border-radius: 12px;
                         box-shadow: 0 8px 25px rgba(0,0,0,0.1); max-width: 700px; margin:auto; }}
                .fail {{ color: #c62828; font-size: 20px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="fail">❌ Verification Failed</div>
                <p>Report ID not found in registry.</p>
                <p><b>ID:</b> {report_id.upper()}</p>
            </div>
        </body>
        </html>
        """

    recomputed = hashlib.sha256(
        (str(record["snapshot"]) + record["generated_at"] + record["model_version"]).encode()
    ).hexdigest()

    verified = recomputed == record["hash"]

    status_color = "#2e7d32" if verified else "#c62828"
    status_icon = "✔ VERIFIED" if verified else "✖ FAILED"

    return f"""
    <html>
    <head>
        <title>Clinical Report Verification</title>
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                background: #eef2f7;
                padding: 50px;
            }}

            .topbar {{
                display:flex;
                justify-content:space-between;
                align-items:center;
                padding:16px;
                border-radius:10px;
                border:1px solid #e5eaf0;
                background:#f9fbfe;
                margin-bottom:25px;
            }}

            .brand {{ display:flex; gap:12px; align-items:center; }}
            .logo {{ width:50px; }}
            .badge {{ width:65px; }}
            .hosp {{ font-size:18px; font-weight:700; color:#0b2a4a; }}
            .tag {{ font-size:12px; color:#6b7280; }}

            .container {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                max-width: 900px;
                margin: auto;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }}

            .status {{
                padding: 18px;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                background: {status_color};
                color: white;
                text-align: center;
                margin-bottom: 30px;
            }}

            .grid {{
                display: grid;
                grid-template-columns: 220px auto;
                row-gap: 14px;
            }}

            .label {{
                font-weight: bold;
                color: #444;
            }}

            .footer {{
                margin-top: 35px;
                font-size: 12px;
                color: #888;
            }}
        </style>
    </head>
    <body>

        <div class="topbar">
            <div class="brand">
                <img src="/static/assets/hospital_logo.png" class="logo"/>
                <div>
                    <div class="hosp">PrecisionPoint Medical Center</div>
                    <div class="tag">CliniSight AI™ Clinical Intelligence Verification Portal</div>
                </div>
            </div>
            <img src="/static/assets/accreditation_badge.png" class="badge"/>
        </div>

        <div class="container">

            <div class="status">
                {status_icon}
            </div>

            <div class="grid">
                <div class="label">Report ID:</div>
                <div>{record["report_id"]}</div>

                <div class="label">Generated At:</div>
                <div>{record["generated_at"]}</div>

                <div class="label">Encounter ID:</div>
                <div>{record["encounter_id"]}</div>

                <div class="label">Model:</div>
                <div>{record["model_name"]} ({record["model_version"]})</div>

                <div class="label">Patient:</div>
                <div>{record.get("patient_name","—")} | DOB: {record.get("dob","—")} | MRN: {record.get("mrn","—")}</div>

                <div class="label">Stored Hash:</div>
                <div style="word-break: break-all;">{record["hash"]}</div>

                <div class="label">Recomputed Hash:</div>
                <div style="word-break: break-all;">{recomputed}</div>
            </div>

            <div class="footer">
                This verification confirms that the report has not been altered since issuance.
                Digital signature uses SHA-256 integrity hashing.
                <br><br>
                CliniSight AI™ Clinical Risk Engine — {record["model_version"]}
            </div>

        </div>
    </body>
    </html>
    """

def get_rule_drivers(observations):
    """
    Returns drivers like 'WBC > 20' with a contribution score.
    This is your 'feature importance' for rule-based models.
    """
    drivers = []
    for obs in observations:
        test = (obs.get("test") or "").upper()
        try:
            value = float(obs.get("value", 0))
        except:
            continue

        if test == "WBC":
            if value > 20:
                drivers.append(("WBC > 20", 2))
            elif value > 11:
                drivers.append(("WBC > 11", 1))

        if test == "HGB":
            if value < 7:
                drivers.append(("HGB < 7", 2))
            elif value < 12:
                drivers.append(("HGB < 12", 1))

    # Aggregate duplicates
    agg = {}
    for name, pts in drivers:
        agg[name] = agg.get(name, 0) + pts

    # Sort highest contribution first
    ranked = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    return ranked

@app.post("/demo/tamper/{report_id}")
def demo_tamper(report_id: str):
    record = get_report_from_db(report_id)
    if not record:
        return JSONResponse({"detail": "Report not found"}, status_code=404)

    # Modify snapshot (tamper)
    snapshot = record["snapshot"]
    snapshot["riskLevel"] = "LOW"  # tamper example
    snapshot["probabilityPercent"] = 5

    # Save tampered snapshot back WITHOUT updating stored hash
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE reports SET snapshot_json = ? WHERE report_id = ?",
        (json.dumps(snapshot), report_id.upper())
    )
    conn.commit()
    conn.close()

    return {"tampered": True, "reportId": report_id.upper()}

# -------------------------
# DOWNLOAD FHIR
# -------------------------
from uuid import uuid4

def to_fhir_bundle(result: dict, report_id: str, encounter_id: str, generated_at: str):
    patient_id = f"patient-{uuid4().hex[:8]}"
    obs_entries = []

    # Patient
    patient = {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"text": result.get("patientName", "Anonymous")}],
    }
    if result.get("dob") and result.get("dob") != "—":
        patient["birthDate"] = result["dob"]

    # Encounter
    encounter = {
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": "finished",
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {"start": generated_at.replace(" ", "T")}
    }

    # Observations
    for obs in result.get("observations", []):
        loinc = obs.get("loinc")
        obs_id = f"obs-{uuid4().hex[:10]}"
        entry = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"},
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc or "unknown",
                    "display": obs.get("test", "Lab Observation")
                }]
            },
            "valueQuantity": {
                "value": float(obs.get("value", 0)) if str(obs.get("value", "")).replace(".","",1).isdigit() else None,
                "unit": obs.get("units", "")
            },
            "referenceRange": [{"text": obs.get("reference_range", "")}],
            "interpretation": [{"text": obs.get("flag", "")}] if obs.get("flag") else []
        }
        obs_entries.append(entry)

    # DiagnosticReport (summary)
    diag = {
        "resourceType": "DiagnosticReport",
        "id": f"report-{report_id}",
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "effectiveDateTime": generated_at.replace(" ", "T"),
        "conclusion": result.get("summary", ""),
        "presentedForm": [{
            "contentType": "text/plain",
            "data": base64.b64encode((result.get("summary","") or "").encode()).decode()
        }]
    }

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": generated_at.replace(" ", "T"),
        "entry": (
            [{"resource": patient}, {"resource": encounter}, {"resource": diag}]
            + [{"resource": o} for o in obs_entries]
        )
    }
    return bundle

@app.get("/download/fhir/bundle")
def download_fhir_bundle():
    global LAST_RESULT
    if not LAST_RESULT:
        return JSONResponse({"detail": "No analysis available"}, status_code=400)
