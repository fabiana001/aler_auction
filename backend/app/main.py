"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers.auctions import router as auctions_router

load_dotenv()

cors_origins_raw = os.getenv("CORS_ORIGINS", '["http://localhost:5173"]')
import json
CORS_ORIGINS = json.loads(cors_origins_raw)

app = FastAPI(
    title="ALER Auction Map API",
    description="API for serving auction data to the interactive map",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auctions_router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
