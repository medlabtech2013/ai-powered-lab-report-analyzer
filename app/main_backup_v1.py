from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uuid

from app.services.hl7_parser import parse_hl7
from app.services.pdf_exporter import generate_lab_report_pdf


app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")

LAST_RESULT = {}
LAB_HISTORY = []
TREND_HISTORY = []

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = await file.read()
    hl7_text = content.decode()

    result = parse_hl7(hl7_text)

    # Store last result
    global LAST_RESULT
    LAST_RESULT = result

    # Append to trend history
    TREND_HISTORY.append({
        "date": result.get("run_date"),
        "observations": result.get("observations", [])
    })

    return result



@app.get("/trends")
async def get_trends():
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

    trends = {}

    for test, values in trend_data.items():
        if len(values) < 2:
            trends[test] = "Not enough data"
            continue

        if values[-1] > values[-2]:
            trends[test] = "Increasing"
        elif values[-1] < values[-2]:
            trends[test] = "Decreasing"
        else:
            trends[test] = "Stable"

    return trends



@app.post("/export/pdf")
async def export_pdf(payload: dict):
    filename = f"lab_report_{uuid.uuid4().hex}.pdf"

    path = generate_lab_report_pdf(
        filename=filename,
        patient_name=payload.get("patient_name"),
        dob=payload.get("dob"),
        mrn=payload.get("mrn"),
        summary=payload.get("summary"),
        observations=payload.get("observations"),
    )

    return FileResponse(path, media_type="application/pdf", filename=filename)

