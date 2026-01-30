from fastapi import APIRouter
from app.events.store import EVENT_STORE

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/")
def list_events():
    return EVENT_STORE.all()
