# app/ingest/rtsp/reader.py

import subprocess
import threading
import time
import logging
import numpy as np
import imageio_ffmpeg

logger = logging.getLogger("RTSPReader")


class RTSPReader(threading.Thread):
    """
    Stage-2 RTSP reader.
    Exactly ONE RTSP connection per camera.
    """

    def __init__(
        self,
        cam_id: str,
        rtsp_url: str,
        frame_hub,
        width: int = 1920,
        height: int = 1080,
        restart_delay: float = 2.0,
    ):
        super().__init__(daemon=True)
        self.cam_id = cam_id
        self.rtsp_url = rtsp_url
        self.frame_hub = frame_hub
        self.width = width
        self.height = height
        self.restart_delay = restart_delay
        self.running = False
        self.process = None

    def _cmd(self):
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        return [
            ffmpeg,
            "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-an",
            "-vf", f"scale={self.width}:{self.height}",
            "-pix_fmt", "bgr24",
            "-f", "rawvideo",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-probesize", "32",
            "-analyzeduration", "0",
            "pipe:1",
        ]

    def run(self):
        self.running = True
        self.frame_hub.register(self.cam_id)

        while self.running:
            try:
                self.process = subprocess.Popen(
                    self._cmd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )

                frame_size = self.width * self.height * 3

                while self.running:
                    raw = self.process.stdout.read(frame_size)
                    if len(raw) != frame_size:
                        break

                    frame = np.frombuffer(raw, np.uint8).reshape(
                        (self.height, self.width, 3)
                    )
                    self.frame_hub.update(self.cam_id, frame)

            except Exception:
                logger.exception(f"[RTSP] {self.cam_id} crashed")

            time.sleep(self.restart_delay)

    def stop(self):
        self.running = False
        if self.process:
            self.process.kill()
