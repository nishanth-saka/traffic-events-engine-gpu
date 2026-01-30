from fastapi import FastAPI
from app.routes import ingest, events, health
from app.ingest.frame.router import router as ingest_router

app = FastAPI(title="Traffic Events Engine")

app.include_router(events.router)
app.include_router(health.router)
app.include_router(ingest_router)