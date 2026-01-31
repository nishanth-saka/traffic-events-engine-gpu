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
    MAIN RTSP reader.
    Pushes frames into FrameHub.
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
        logger.info("[RTSP] Connecting MAIN stream: %s", self.cam_id)
        self.running = True
        self.frame_hub.register(self.cam_id)

        frame_size = self.width * self.height * 3
        buffer = bytearray()

        while self.running:
            try:
                self.process = subprocess.Popen(
                    self._cmd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=10**8,  # 🛡️ large buffer to avoid stalls
                )

                while self.running:
                    chunk = self.process.stdout.read(4096)
                    if not chunk:
                        break

                    buffer.extend(chunk)

                    while len(buffer) >= frame_size:
                        frame_bytes = buffer[:frame_size]
                        buffer = buffer[frame_size:]

                        frame = np.frombuffer(
                            frame_bytes, np.uint8
                        ).reshape((self.height, self.width, 3))

                        self.frame_hub.update(self.cam_id, frame)

            except Exception:
                logger.exception("[RTSP] Crash on %s", self.cam_id)

            time.sleep(self.restart_delay)
