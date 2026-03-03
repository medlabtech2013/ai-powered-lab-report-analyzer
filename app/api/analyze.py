from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.services.parser import parse_lab
from app.services.summary import generate_summary
from app.services.fhir import build_fhir_bundle
from app.services.pdf_exporter import generate_lab_report_pdf
from app.services.clinical_summary import generate_summary

router = APIRouter()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="ignore")

    observations = parse_lab(content)
    clinical_summary = generate_summary(observations)
    clinical_summary = generate_summary(parsed_results)
    fhir_bundle = build_fhir_bundle(observations)

    return {
	return {
	"status": "success",
    	"clinical_summary": clinical_summary,
    	"fhir_version": "R4",
    	"bundle": bundle
    }

        "observations": observations,
        "clinical_summary": clinical_summary,
        "fhir": fhir_bundle
    }

@router.post("/export/pdf")
async def export_pdf(
    file: UploadFile = File(...),
    name: str = Form(...),
    dob: str = Form(...),
    mrn: str = Form(...)
):
    content = (await file.read()).decode("utf-8", errors="ignore")

    observations = parse_lab(content)
    clinical_summary = generate_summary(observations)

    pdf_path, pdf_filename = generate_lab_report_pdf(
        observations=observations,
        clinical_summary=clinical_summary,
        patient_name=name,
        patient_dob=dob,
        patient_mrn=mrn,
        source_filename=file.filename
    )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_filename
    )
