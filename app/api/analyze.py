from fastapi import APIRouter, UploadFile, File
from app.services.parser import parse_lab
from app.services.summary import generate_summary


router = APIRouter()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="ignore")

    parsed_results = parse_lab(content)

    clinical_summary = generate_summary(parsed_results)

    return {
        "filename": file.filename,
        "observation_count": len(parsed_results),
        "observations": parsed_results,
        "clinical_summary": clinical_summary
    }

