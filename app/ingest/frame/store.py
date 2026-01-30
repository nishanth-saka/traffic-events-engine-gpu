# app/ingest/frame/store.py

class FrameStore:
    """
    In-memory overwrite-only frame store.
    - One latest frame per camera
    - Data-only (no business logic)
    """

    def __init__(self):
        self._frames = {}

    def update(self, *, camera_id: str, frame, ts: float):
        self._frames[camera_id] = {
            "frame": frame,
            "ts": ts,
        }

    def get(self, camera_id: str):
        return self._frames.get(camera_id)

    def camera_ids(self):
        return list(self._frames.keys())


# 🔒 Singleton (safe: data-only)
frame_store = FrameStore()
