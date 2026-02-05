from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter()

@router.post("/analyze")
async def analyze_lab_report(file: UploadFile = File(...)):
    # 1️⃣ Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        # 2️⃣ Read + decode file safely
        raw_bytes = await file.read()
        text = raw_bytes.decode("utf-8", errors="ignore")

        if not text.strip():
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # 3️⃣ Split HL7 segments
        segments = text.split("\n")

        observations = []

        for line in segments:
            # Look for OBX segments
            if line.startswith("OBX"):
                fields = line.split("|")

                # Safe indexing
                test_name = fields[3] if len(fields) > 3 else "Unknown Test"
                value = fields[5] if len(fields) > 5 else "N/A"
                units = fields[6] if len(fields) > 6 else ""
                reference = fields[7] if len(fields) > 7 else ""

                observations.append({
                    "test": test_name,
                    "value": value,
                    "units": units,
                    "reference_range": reference
                })

        # 4️⃣ Return structured response
        return {
            "filename": file.filename,
            "observation_count": len(observations),
            "observations": observations
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

