import logging

logging.basicConfig(level=logging.INFO)

# 🔒 EARLY dependency sanity check (before FastAPI imports anything else)
try:
    import numpy as np
    logging.info(f"[BOOT] NumPy version = {np.__version__}")
except Exception as e:
    logging.exception("[BOOT] NumPy import failed")
    raise

from fastapi import FastAPI
from app.routes import ingest, events, health
from app.ingest.frame.router import router as ingest_router

app = FastAPI(title="Traffic Events Engine")

app.include_router(events.router)
app.include_router(health.router)
app.include_router(ingest_router)
