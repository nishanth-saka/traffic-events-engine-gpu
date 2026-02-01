# app/detection/detector.py

import time
import threading
import logging

from app.detection.vehicle_detector import detect_vehicles
from app.ingest.frame.pipeline import process_frame

logger = logging.getLogger("DetectionWorker")


class DetectionWorker(threading.Thread):
    """
    Stage-1 FPS-controlled detection worker (REAL VEHICLE DETECTION).

    Guarantees:
    - Pulls ONLY latest frame from FrameHub (MAIN stream)
    - Drops frames by design
    - Runs at low, controlled FPS
    - Publishes VEHICLE METADATA ONLY
    - NO plates in metadata (plates handled by Phase-A pipeline)
    """

    def __init__(
        self,
        cam_id: str,
        frame_hub,
        detection_manager,
        fps: int = 2,
        anpr_fps: float = 0.7,          # Opt-1: separate ANPR throttle
        vehicle_delta: int = 1,         # Opt-2: min change to retrigger ANPR
        per_vehicle_cooldown: float = 2.0,  # Opt-3: per-vehicle cooldown
    ):
        super().__init__(daemon=True)

        self.cam_id = cam_id
        self.frame_hub = frame_hub
        self.detection_manager = detection_manager

        # -----------------------------
        # Detection FPS
        # -----------------------------
        self.interval = 1.0 / max(fps, 1)

        # -----------------------------
        # ANPR optimisations
        # -----------------------------
        self.anpr_interval = 1.0 / max(anpr_fps, 0.1)
        self.vehicle_delta = vehicle_delta
        self.per_vehicle_cooldown = per_vehicle_cooldown

        self._last_anpr_ts = 0.0
        self._last_vehicle_count = 0
        self._vehicle_last_seen = {}   # vehicle_id -> last_ts

        self.running = True
        self._last_run = 0.0

        logger.info(
            "[DETECT] config | cam=%s detect_fps=%.1f anpr_fps=%.1f "
            "vehicle_delta=%d cooldown=%.1fs",
            self.cam_id,
            1.0 / self.interval,
            1.0 / self.anpr_interval,
            self.vehicle_delta,
            self.per_vehicle_cooldown,
        )

    def run(self):
        logger.info(
            "[DETECT] Vehicle worker started for %s @ %.1f FPS",
            self.cam_id,
            1.0 / self.interval,
        )

        while self.running:
            now = time.time()

            # -----------------------------
            # FPS throttle
            # -----------------------------
            if now - self._last_run < self.interval:
                time.sleep(0.01)
                continue

            self._last_run = now

            frame = self.frame_hub.get_latest(self.cam_id)
            if frame is None:
                continue

            try:
                # ---------------------------------------------
                # 1️⃣ Vehicle detection
                # ---------------------------------------------
                vehicles = detect_vehicles(frame)

                if not vehicles:
                    self._last_vehicle_count = 0
                    logger.debug(
                        "[DETECT] %s no vehicles detected",
                        self.cam_id,
                    )
                    continue

                vehicle_count = len(vehicles)

                # ---------------------------------------------
                # 2️⃣ Publish VEHICLE metadata ONLY
                # ---------------------------------------------
                self.detection_manager.update(
                    self.cam_id,
                    vehicles=vehicles,
                    plates=[],   # 🔒 plates intentionally empty
                )

                logger.info(
                    "[DETECT] %s heartbeat | vehicles=%d",
                    self.cam_id,
                    vehicle_count,
                )

                # ---------------------------------------------
                # Opt-1: global ANPR throttle
                # ---------------------------------------------
                if now - self._last_anpr_ts < self.anpr_interval:
                    continue

                # ---------------------------------------------
                # Opt-2: vehicle-count delta trigger
                # ---------------------------------------------
                if abs(vehicle_count - self._last_vehicle_count) < self.vehicle_delta:
                    continue

                # ---------------------------------------------
                # Opt-3: per-vehicle cooldown
                # ---------------------------------------------
                eligible_vehicles = []
                for v in vehicles:
                    vid = v.get("id") or tuple(v.get("bbox", []))
                    last_seen = self._vehicle_last_seen.get(vid, 0.0)

                    if now - last_seen >= self.per_vehicle_cooldown:
                        eligible_vehicles.append(v)
                        self._vehicle_last_seen[vid] = now

                if not eligible_vehicles:
                    continue

                # ---------------------------------------------
                # 3️⃣ Phase-A ANPR pipeline (SIDE-EFFECT ONLY)
                # ---------------------------------------------
                logger.info(
                    "[ANPR] frame received | cam=%s vehicles=%d",
                    self.cam_id,
                    len(eligible_vehicles),
                )

                process_frame(
                    camera_id=self.cam_id,
                    frame_ts=now,
                    frame=frame,
                    vehicles=eligible_vehicles,
                    frame_store=None,   # safe placeholder
                )

                self._last_anpr_ts = now
                self._last_vehicle_count = vehicle_count

            except Exception:
                logger.exception(
                    "[DETECT] Crash in detection pipeline on %s",
                    self.cam_id,
                )
