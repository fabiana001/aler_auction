"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.pipeline.manager import PipelineManager
from app.routers.auctions import router as auctions_router
from app.routers.pipeline import router as pipeline_router

load_dotenv()

cors_origins_raw = os.getenv("CORS_ORIGINS", '["http://localhost:5173"]')
CORS_ORIGINS = json.loads(cors_origins_raw)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pipeline_manager = PipelineManager()
    yield


app = FastAPI(
    title="ALER Auction Map API",
    description="API for serving auction data to the interactive map",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auctions_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
