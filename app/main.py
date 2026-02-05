from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.analyze import router as analyze_router

app = FastAPI(
    title="AI-Powered Lab Report Analyzer",
    version="0.1.0"
)

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(analyze_router)

# API health check (moved)
@app.get("/api/health")
def health():
    return {"status": "API is running"}

# Frontend (NOW owns /)
app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)

