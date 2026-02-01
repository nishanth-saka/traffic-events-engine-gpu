# app/detection/detector.py
import time
import threading
import logging

from app.detection.vehicle_detector import detect_vehicles
from app.ingest.frame.pipeline import run_frame_pipeline

logger = logging.getLogger("DetectionWorker")


class DetectionWorker(threading.Thread):
    """
    Stage-1 FPS-controlled detection worker.
    """

    def __init__(
        self,
        cam_id: str,
        frame_hub,
        detection_manager,
        fps: int = 2,
        anpr_fps: float = 0.7,
        vehicle_delta: int = 1,
        per_vehicle_cooldown: float = 2.0,
    ):
        super().__init__(daemon=True)

        self.cam_id = cam_id
        self.frame_hub = frame_hub
        self.detection_manager = detection_manager

        self.interval = 1.0 / max(fps, 1)
        self.anpr_interval = 1.0 / max(anpr_fps, 0.1)

        self.vehicle_delta = vehicle_delta
        self.per_vehicle_cooldown = per_vehicle_cooldown

        self._last_run = 0.0
        self._last_anpr_ts = 0.0
        self._last_vehicle_count = 0
        self._vehicle_last_seen = {}

        self.running = True

    def run(self):
        logger.info("[DETECT] started | cam=%s", self.cam_id)

        while self.running:
            now = time.time()

            if now - self._last_run < self.interval:
                time.sleep(0.01)
                continue
            self._last_run = now

            frame = self.frame_hub.get_latest(self.cam_id)
            if frame is None:
                continue

            try:
                vehicles = detect_vehicles(frame)
                count = len(vehicles)

                self.detection_manager.update(
                    self.cam_id,
                    vehicles=vehicles,
                    plates=[],
                )

                if not vehicles:
                    self._last_vehicle_count = 0
                    continue

                if now - self._last_anpr_ts < self.anpr_interval:
                    continue

                if abs(count - self._last_vehicle_count) < self.vehicle_delta:
                    continue

                eligible = []
                for v in vehicles:
                    vid = tuple(v["bbox"])
                    last_seen = self._vehicle_last_seen.get(vid, 0.0)
                    if now - last_seen >= self.per_vehicle_cooldown:
                        eligible.append(v)
                        self._vehicle_last_seen[vid] = now

                if not eligible:
                    continue

                run_frame_pipeline(
                    camera_id=self.cam_id,
                    frame_ts=now,
                    frame=frame,
                    vehicles=eligible,
                )

                self._last_anpr_ts = now
                self._last_vehicle_count = count

            except Exception:
                logger.exception("[DETECT] crash | cam=%s", self.cam_id)
