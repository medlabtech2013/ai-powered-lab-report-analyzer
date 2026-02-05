from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.analyze import router as analyze_router

app = FastAPI(
    title="AI-Powered Lab Report Analyzer",
    version="0.1.0"
)

# API routes
app.include_router(analyze_router)

# Serve static files (optional, future use)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# FRONTEND ROOT
@app.get("/")
def root():
    return FileResponse("frontend/index.html")

