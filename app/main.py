from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.analyze import router as analyze_router

app = FastAPI(
    title="AI-Powered Lab Report Analyzer",
    version="0.1.0"
)

# ✅ CORS (THIS IS THE FIX)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for demo / portfolio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(analyze_router)

# Root health check
@app.get("/")
def root():
    return {"status": "API is running"}

# Frontend static files
app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)

