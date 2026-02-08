from abc import ABC, abstractmethod
from typing import Any


class FrameProvider(ABC):
    @abstractmethod
    def get_frame(self, camera_id: str) -> Any:
        pass
