from __future__ import annotations

from pathlib import Path

from .otbm_deserializer import OtbmDeserializer
from .otbm_validator import OtbmValidator


class OtbmReader:
    def __init__(self):
        self.deserializer = OtbmDeserializer()
        self.validator = OtbmValidator()

    def read(self, file_path: str | Path):
        path = Path(file_path)
        data = path.read_bytes()
        self.validator.validate(data)
        return self.deserializer.deserialize(data)
