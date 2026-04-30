from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.recalls import router as recalls_router

app = FastAPI(
    title="MedSignal AI API",
    description="Healthcare safety intelligence API for recalls, adverse-event signals, and environmental health context.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recalls_router, prefix="/api/v1/recalls", tags=["RecallRadar"])


@app.get("/")
def root():
    return {
        "message": "MedSignal AI backend is running",
        "status": "ok",
        "module": "RecallRadar",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
