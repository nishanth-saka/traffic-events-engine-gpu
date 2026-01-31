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
    STAGE 1 RTSP Reader

    - EXACTLY one RTSP connection per camera
    - MAIN stream only
    - Overwrite-only frame delivery
    """

    def __init__(
        self,
        cam_id: str,
        rtsp_url: str,
        frame_store,
        width: int = 1920,
        height: int = 1080,
        restart_delay: float = 2.0,
    ):
        super().__init__(daemon=True)

        self.cam_id = cam_id
        self.rtsp_url = rtsp_url
        self.frame_store = frame_store
        self.width = width
        self.height = height
        self.restart_delay = restart_delay

        self.running = False
        self.process = None

    def _ffmpeg_cmd(self):
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        return [
            ffmpeg,
            "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-an",
            "-sn",
            "-dn",
            "-vf", f"scale={self.width}:{self.height}",
            "-pix_fmt", "bgr24",
            "-f", "rawvideo",
            "pipe:1",
        ]

    def run(self):
        self.running = True

        while self.running:
            try:
                logger.info(f"[RTSP] Connecting MAIN stream: {self.cam_id}")

                self.process = subprocess.Popen(
                    self._ffmpeg_cmd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=10**8,
                )

                frame_size = self.width * self.height * 3

                while self.running:
                    raw = self.process.stdout.read(frame_size)
                    if len(raw) != frame_size:
                        raise RuntimeError("Incomplete frame read")

                    frame = np.frombuffer(raw, np.uint8).reshape(
                        (self.height, self.width, 3)
                    )

                    self.frame_store.update(self.cam_id, frame)

            except Exception as e:
                logger.warning(
                    f"[RTSP] Stream error ({self.cam_id}): {e}. Restarting..."
                )
                time.sleep(self.restart_delay)

            finally:
                if self.process:
                    self.process.kill()
                    self.process = None

    def stop(self):
        self.running = False
        if self.process:
            self.process.kill()
            self.process = None
