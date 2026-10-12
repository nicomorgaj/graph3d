from __future__ import annotations

import colorsys
import struct
import zlib
from pathlib import Path

import numpy as np


def _color(area: dict, community: int) -> tuple[float, float, float]:
    if area.get("gray"):
        hue, sat, light = 215 / 360, 0.12, 0.58
    else:
        hue = ((area["hue"] + (((community * 37) % 31) - 15)) % 360) / 360
        sat, light = 0.7, (52 + ((community * 13) % 5) * 4) / 100
    r, g, b = colorsys.hls_to_rgb(hue, light, sat)
    return r * 255, g * 255, b * 255


def _png(path: Path, image: np.ndarray) -> None:
    height, width, _ = image.shape
    raw = b"".join(b"\x00" + image[y].clip(0, 255).astype(np.uint8).tobytes() for y in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def render_png(payload: dict, path: str | Path, yaw: float = 0.6, pitch: float = -0.3, width: int = 1500, height: int = 950) -> None:
    """Vista previa estática (sin navegador): mismos colores y proyección que el visor."""
    nodes, edges, areas, radius = payload["nodes"], payload["edges"], payload["areas"], payload["R"]
    points = np.array([n["p"] for n in nodes], dtype=np.float64).reshape(-1, 3)
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    x1 = points[:, 0] * cy + points[:, 2] * sy
    z1 = -points[:, 0] * sy + points[:, 2] * cy
    y1 = points[:, 1] * cp - z1 * sp
    fov = 700.0

    def project(dist):
        z2 = points[:, 1] * sp + z1 * cp + dist
        scale = fov / z2
        return z2, scale, width / 2 + x1 * scale, height / 2 + y1 * scale

    low, high = 60.0, max(radius * 8, 800.0)
    for _ in range(18):
        mid = (low + high) / 2
        z2, scale, xs, ys = project(mid)
        inside = (z2 > 20).all() and (np.abs(xs - width / 2) <= width * 0.47).all() and (np.abs(ys - height / 2) <= height * 0.47).all()
        low, high = (low, mid) if inside else (mid, high)
    z2, scale, xs, ys = project(high)

    image = np.zeros((height, width, 3), dtype=np.float32)
    image[:] = (10, 14, 22)

    def put(px, py, color, alpha):
        xi, yi = np.clip(px.astype(int), 0, width - 1), np.clip(py.astype(int), 0, height - 1)
        image[yi, xi] = image[yi, xi] * (1 - alpha) + np.array(color) * alpha

    if edges:
        pairs = np.array([(e[0], e[1]) for e in edges])
        t = np.linspace(0, 1, 14)[None, :]
        ex = xs[pairs[:, 0]][:, None] * (1 - t) + xs[pairs[:, 1]][:, None] * t
        ey = ys[pairs[:, 0]][:, None] * (1 - t) + ys[pairs[:, 1]][:, None] * t
        inter = np.array([nodes[a]["c"] != nodes[b]["c"] for a, b in pairs])
        put(ex[~inter].ravel(), ey[~inter].ravel(), (140, 160, 196), 0.12)
        put(ex[inter].ravel(), ey[inter].ravel(), (185, 200, 230), 0.28)

    for i in np.argsort(-z2):
        node = nodes[i]
        r = max(1, int(round((1.7 + np.sqrt(node["d"]) * 0.8) * scale[i] * 0.85)))
        color = _color(areas[node["a"]], node["c"])
        cx, cy_ = int(xs[i]), int(ys[i])
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r and 0 <= cx + dx < width and 0 <= cy_ + dy < height:
                    image[cy_ + dy, cx + dx] = color
    _png(Path(path), image)
