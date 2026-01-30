from fastapi import APIRouter, UploadFile, File, Form
from datetime import datetime
import uuid

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/frame")
async def ingest_frame(
    camera_id: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Phase 0:
    - Accepts an image
    - Treats it as a frame
    - Pushes into detection pipeline
    """
    frame_id = str(uuid.uuid4())

    # TODO:
    # 1. decode image
    # 2. run detection
    # 3. feed temporal engine

    return {
        "status": "accepted",
        "frame_id": frame_id,
        "camera_id": camera_id,
        "timestamp": datetime.utcnow(),
    }
