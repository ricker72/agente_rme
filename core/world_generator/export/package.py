from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Mapping

from .serializer import fingerprint_bytes

ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def write_deterministic_zip(path: Path, files: Mapping[str, bytes]) -> str:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, files[name])
    return fingerprint_bytes(path.read_bytes())
