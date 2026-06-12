from __future__ import annotations

from typing import Any, Dict

from .otbm_serializer import OtbmSerializer


class OtbmDeserializer:
    """
    Deserializes OTBM binary data back into a structured dictionary.

    Uses OtbmSerializer.deserialize() which handles the real OTBM format.
    """

    def __init__(self):
        self.serializer = OtbmSerializer()

    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """
        Deserialize OTBM bytes into a dict.

        Returns:
            dict with keys: version, width, height, item_version, tiles,
            spawns, towns, waypoints, description, spawn_file, house_file
        """
        return self.serializer.deserialize(data)
