from fastapi import APIRouter, UploadFile, File
import shutil
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Simplified clinical reference ranges
NORMAL_RANGES = {
    "WBC": (4.0, 11.0, "10^3/uL"),
    "HGB": (12.0, 17.5, "g/dL"),
    "PLT": (150, 450, "10^3/uL")
}

def build_fhir_observation(test, value, unit):
    return {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory"
                    }
                ]
            }
        ],
        "code": {
            "text": test
        },
        "valueQuantity": {
            "value": value,
            "unit": unit
        }
    }

def interpret_lab(text: str):
    results = []
    clinical_summary = []
    fhir_observations = []

    for test, (low, high, unit) in NORMAL_RANGES.items():
        if test in text:
            for word in text.replace(":", " ").split():
                try:
                    value = float(word)

                    # Human-readable result
                    if value < low:
                        results.append(f"{test} LOW: {value}")
                        clinical_summary.append(
                            f"{test} is below the normal reference range and may require further evaluation."
                        )
                    elif value > high:
                        results.append(f"{test} HIGH: {value}")
                        clinical_summary.append(
                            f"{test} is above the normal reference range and may indicate an abnormal finding."
                        )
                    else:
                        results.append(f"{test} NORMAL: {value}")

                    # FHIR Observation
                    fhir_observations.append(
                        build_fhir_observation(test, value, unit)
                    )

                except ValueError:
                    continue

    if not results:
        results.append("No recognizable lab values found.")
        clinical_summary.append("No abnormal laboratory findings were detected.")

    return results, clinical_summary, fhir_observations


@router.post("/analyze")
async def analyze_lab_report(file: UploadFile = File(...)):
    file_path = f"{UPLOAD_DIR}/{file.filename}"

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read file content
    with open(file_path, "r", errors="ignore") as f:
        content = f.read()

    results, summary, observations = interpret_lab(content)

    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": obs} for obs in observations]
    }

    return {
        "filename": file.filename,
        "analysis": results,
        "clinical_summary": summary,
        "fhir_bundle": fhir_bundle
    }

