from __future__ import annotations

NODE_START = 0xFE
NODE_END = 0xFF
ESCAPE_BYTE = 0xFD
RESERVED_BYTES = {NODE_START, NODE_END, ESCAPE_BYTE}


def escape_otbm_bytes(data: bytes) -> bytes:
    out = bytearray()
    for value in data:
        if value in RESERVED_BYTES:
            out.extend((ESCAPE_BYTE, value))
        else:
            out.append(value)
    return bytes(out)


def unescape_otbm_bytes(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        value = data[i]
        if value == ESCAPE_BYTE:
            if i + 1 >= len(data):
                raise ValueError("dangling OTBM escape byte")
            out.append(data[i + 1])
            i += 2
        else:
            out.append(value)
            i += 1
    return bytes(out)
