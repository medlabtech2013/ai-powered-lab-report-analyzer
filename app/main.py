from fastapi import FastAPI
from app.api.analyze import router as analyze_router

app = FastAPI(title="AI-Powered Lab Report Analyzer")

app.include_router(analyze_router)

@app.get("/")
def root():
    return {"status": "API is running"}

