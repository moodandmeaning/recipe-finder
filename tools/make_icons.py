"""Draws the app icons (a white leaf on green) with no dependencies. Run: python tools/make_icons.py"""
import math
import struct
import zlib
from pathlib import Path

GREEN = (47, 125, 79)
WHITE = (255, 255, 255)
OUT = Path(__file__).resolve().parent.parent / "icons"


def inside_leaf(x, y):
    # Coordinates in 0..1. Leaf = intersection of two circles, rotated 45 degrees.
    cx, cy = x - 0.5, y - 0.5
    a = math.radians(45)
    u = cx * math.cos(a) - cy * math.sin(a)
    v = cx * math.sin(a) + cy * math.cos(a)
    r, off = 0.30, 0.17
    in_leaf = (u - off) ** 2 + v ** 2 < r ** 2 and (u + off) ** 2 + v ** 2 < r ** 2
    vein = abs(u) < 0.012 and abs(v) < 0.24
    stem = abs(u) < 0.014 and 0.20 < v < 0.30
    return (in_leaf and not vein) or stem


def png(size, path):
    ss = 3  # supersampling for smooth edges
    rows = []
    for py in range(size):
        row = bytearray([0])
        for px in range(size):
            hits = sum(
                inside_leaf((px + (i + 0.5) / ss) / size, (py + (j + 0.5) / ss) / size)
                for i in range(ss) for j in range(ss)
            )
            f = hits / (ss * ss)
            row += bytes(round(GREEN[k] * (1 - f) + WHITE[k] * f) for k in range(3))
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", raw)
        + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for size, name in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")]:
        png(size, OUT / name)
        print("wrote", name)
