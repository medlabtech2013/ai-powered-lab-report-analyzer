from fastapi import APIRouter, UploadFile, File
from app.services.parser import parse_lab
from app.core.loinc_map import LOINC_MAP

router = APIRouter()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="ignore")
    parsed_results = parse_lab(content)

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }

    for item in parsed_results:
        test_name = item["test"]
        value_raw = item["value"]

        loinc = LOINC_MAP.get(test_name, {})

        observation = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc.get("code", "unknown"),
                    "display": test_name
                }]
            },
            "valueString": value_raw
        }

        if value_raw.replace(".", "", 1).isdigit():
            observation["valueQuantity"] = {
                "value": float(value_raw),
                "unit": loinc.get("unit", ""),
                "system": "http://unitsofmeasure.org"
            }
            observation.pop("valueString")

        bundle["entry"].append({"resource": observation})

    return {
        "source": "AI-Powered Lab Report Analyzer",
        "format": "FHIR-R4",
        "bundle": bundle
    }

