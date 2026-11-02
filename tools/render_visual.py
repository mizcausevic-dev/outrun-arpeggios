"""Procedural raster artwork and ffmpeg media steps.

The painter is original and deterministic. It draws a sunset grid: a horizon,
a sun, perspective lines, and a skyline whose heights follow an arpeggio
accent contour. It is an illustration, not a photograph of a session or of
performers.

DejaVu Sans Bold is used only to rasterize the disclosure into the film and the
poster. The font file is not shipped.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ON_PICTURE = "preview, not master"


def _clamp(value: int) -> int:
    return 0 if value < 0 else 255 if value > 255 else value


def _mix(a, b, t):
    return int(a + (b - a) * t)


def paint(width: int, height: int, framing: str) -> bytes:
    levels = (
        (0.34, 0.48, 0.72, 0.96, 0.58, 0.40, 0.66, 0.88, 1.00, 0.62, 0.46, 0.74, 0.90, 0.52, 0.38, 0.70)
        if framing == "wide"
        else (0.42, 0.70, 1.00, 0.55, 0.86, 0.48, 0.76, 0.94, 0.60, 0.36, 0.82, 0.50)
    )
    horizon = int(height * (0.58 if framing == "wide" else 0.52))
    sun_x = int(width * (0.72 if framing == "wide" else 0.38))
    sun_y = int(horizon - height * (0.16 if framing == "wide" else 0.12))
    sun_r = int(height * (0.16 if framing == "wide" else 0.13))
    floor = int(height * (0.90 if framing == "wide" else 0.88))
    pixels = bytearray(width * height * 3)
    for y in range(height):
        row = y * width * 3
        if y < horizon:
            t = y / max(1, horizon)
            r = _mix(18, 186, t * t)
            g = _mix(8, 54, t)
            b = _mix(48, 92, t)
        else:
            t = (y - horizon) / max(1, height - horizon)
            r = _mix(92, 22, t)
            g = _mix(24, 8, t)
            b = _mix(48, 28, t)
        for x in range(width):
            pixels[row + x * 3] = r
            pixels[row + x * 3 + 1] = g
            pixels[row + x * 3 + 2] = b
    for y in range(max(0, sun_y - sun_r * 2), min(height, sun_y + sun_r)):
        row = y * width * 3
        for x in range(max(0, sun_x - sun_r * 2), min(width, sun_x + sun_r * 2)):
            dx = x - sun_x
            dy = y - sun_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= sun_r:
                pixels[row + x * 3] = 255
                pixels[row + x * 3 + 1] = 214
                pixels[row + x * 3 + 2] = 120
            elif dist <= sun_r * 1.7 and y < horizon:
                glow = 1.0 - (dist - sun_r) / (sun_r * 0.7)
                pixels[row + x * 3] = _clamp(pixels[row + x * 3] + int(80 * glow))
                pixels[row + x * 3 + 1] = _clamp(pixels[row + x * 3 + 1] + int(36 * glow))
    vanish_x = width * (0.50 if framing == "wide" else 0.46)
    vanish_y = horizon
    for y in range(horizon, height):
        depth = (y - vanish_y) / max(1, height - vanish_y)
        inv = 1.0 / max(depth, 0.035)
        horizontal = abs(inv - round(inv)) < (0.055 if framing == "wide" else 0.07)
        row = y * width * 3
        for x in range(width):
            slope = (x - vanish_x) / max(1.0, y - vanish_y)
            slot = slope * (7 if framing == "wide" else 5)
            vertical = abs(slot - round(slot)) < 0.045
            if horizontal or vertical:
                hot = 0.35 + 0.65 * (1.0 - depth)
                pixels[row + x * 3] = _clamp(int(pixels[row + x * 3] * 0.45 + (255 * hot)))
                pixels[row + x * 3 + 1] = _clamp(int(pixels[row + x * 3 + 1] * 0.45 + (70 * hot)))
                pixels[row + x * 3 + 2] = _clamp(int(pixels[row + x * 3 + 2] * 0.55 + (150 * hot)))
    margin_x = int(width * (0.06 if framing == "wide" else 0.08))
    span = max(1, width - margin_x * 2)
    gap = span / len(levels)
    for index, level in enumerate(levels):
        x0 = int(margin_x + index * gap + gap * 0.22)
        x1 = int(margin_x + index * gap + gap * 0.78)
        y0 = int(floor - level * (floor - horizon - 8))
        for y in range(max(0, y0), min(height, floor)):
            mix = (y - y0) / max(1, floor - y0)
            if level > 0.92:
                r, g, b = 255, 90 + int(40 * mix), 70
            elif level > 0.7:
                r, g, b = 255, 122, 60
            else:
                r, g, b = 255, 190, 90
            row = y * width * 3
            for x in range(max(0, x0), min(width, x1)):
                pixels[row + x * 3] = r
                pixels[row + x * 3 + 1] = g
                pixels[row + x * 3 + 2] = b
    return bytes(pixels)

def write_ppm(path: Path, width: int, height: int, rgb: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + rgb)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            + " ".join(command)
            + "\n"
            + completed.stderr[-2000:]
        )


def ppm_to_jpeg(ppm: Path, jpeg: Path, quality: int = 3) -> None:
    jpeg.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", "-q:v", str(quality), str(jpeg)])


def draw_disclosure(source: Path, dest: Path, textfile: Path) -> list[str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y", "-i", str(source),
        "-vf",
        (
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-frames:v", "1",
        "-q:v", "3",
        str(dest),
    ]
    run(command)
    return command


def encode_mp3(wav: Path, mp3: Path) -> list[str]:
    mp3.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-i", str(wav),
        "-codec:a", "libmp3lame", "-b:a", "192k",
        str(mp3),
    ]
    run(command)
    return command


def encode_film(plate: Path, mp3: Path, mp4: Path, textfile: Path, duration: str) -> list[str]:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "24", "-i", str(plate),
        "-i", str(mp3),
        "-t", duration,
        "-vf",
        (
            "scale=1280:720,"
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-r", "24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(mp4),
    ]
    run(command)
    return command


def derive_social(hero: Path, square: Path, portrait: Path, card: Path) -> dict[str, list[str]]:
    portrait.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    portrait_cmd = [
        "ffmpeg", "-y", "-i", str(square),
        "-vf", "crop=864:1080:108:0,scale=1080:1350",
        "-q:v", "3",
        str(portrait),
    ]
    card_cmd = [
        "ffmpeg", "-y", "-i", str(hero),
        "-vf", "scale=1600:900",
        "-q:v", "3",
        str(card),
    ]
    run(portrait_cmd)
    run(card_cmd)
    return {"portrait": portrait_cmd, "card": card_cmd}
