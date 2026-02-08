# app/routes/debug_plates.py

import os
import glob
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

DEBUG_DIR = "/tmp/plate_debug"

router = APIRouter(prefix="/debug/plates", tags=["debug"])


def _latest_image():
    files = sorted(
        glob.glob(os.path.join(DEBUG_DIR, "*.jpg")),
        key=os.path.getmtime,
        reverse=True,
    )
    return files[0] if files else None


@router.get("/latest")
def get_latest_plate_debug():
    """
    Return the most recent plate debug image.
    """

    img = _latest_image()
    if not img:
        raise HTTPException(status_code=404, detail="No debug images available")

    return FileResponse(
        img,
        media_type="image/jpeg",
        filename=os.path.basename(img),
    )


@router.get("/latest/full")
def get_latest_plate_debug_full():
    """
    Return metadata for latest debug image + image reference.
    """

    img = _latest_image()
    if not img:
        raise HTTPException(status_code=404, detail="No debug images available")

    meta_path = img.replace(".jpg", ".json")
    meta = None

    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)

    return {
        "image_endpoint": "/debug/plates/latest",
        "metadata": meta,
    }


@router.delete("/purge")
def purge_plate_debug():
    """
    Delete all plate debug images + metadata.
    """

    if not os.path.exists(DEBUG_DIR):
        return {"deleted": 0}

    files = glob.glob(os.path.join(DEBUG_DIR, "*"))
    deleted = 0

    for f in files:
        try:
            os.remove(f)
            deleted += 1
        except Exception:
            pass

    return {
        "deleted": deleted,
        "path": DEBUG_DIR,
    }
