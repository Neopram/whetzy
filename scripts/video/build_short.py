"""Monta un short vertical (1080x1920) a partir de capturas reales y voz Piper.

Uso:
  python build_short.py escenas_es.json --shots DIR --voice MODEL.onnx --out short_es.mp4

Cada escena es una captura de la app (con zoom lento) o un rótulo, con su
narración. La duración de la escena es max(voz + 0,6 s, min_s). Sin música:
no hay pista con licencia verificada para este uso.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (7, 11, 20)
ACCENT = (34, 211, 238)
WHITE = (245, 247, 250)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FF = imageio_ffmpeg.get_ffmpeg_exe()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def wrap(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int
) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            test = f"{cur} {word}".strip()
            if draw.textlength(test, font=font) <= width:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def title_card(scene: dict, path: Path) -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line(
            [(0, y), (W, y)], fill=(int(7 + 6 * t), int(11 + 40 * t), int(20 + 45 * t))
        )
    brand = ImageFont.truetype(FONT_BOLD, 64)
    d.text((W / 2, 300), "Whetzy", font=brand, fill=ACCENT, anchor="mm")
    big = ImageFont.truetype(FONT_BOLD, 92)
    lines = wrap(d, scene["titulo"], big, W - 160)
    y = H / 2 - (len(lines) * 118) / 2
    for line in lines:
        d.text((W / 2, y), line, font=big, fill=WHITE, anchor="mm")
        y += 118
    if scene.get("pie"):
        small = ImageFont.truetype(FONT, 46)
        d.text((W / 2, H - 260), scene["pie"], font=small, fill=ACCENT, anchor="mm")
    img.save(path)


def caption_overlay(text: str, path: Path) -> None:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_BOLD, 58)
    lines = wrap(d, text, font, W - 140)
    band_h = 90 + len(lines) * 74
    d.rectangle([0, 0, W, band_h], fill=(7, 11, 20, 235))
    d.rectangle([0, band_h - 8, W, band_h], fill=ACCENT + (255,))
    y = 60
    for line in lines:
        d.text((W / 2, y + 30), line, font=font, fill=WHITE, anchor="mm")
        y += 74
    img.save(path)


def scene_clip(scene: dict, shots: Path, voice: Path, work: Path) -> Path:
    sid = scene["id"]
    wav = work / f"{sid}.wav"
    run(
        ["python3", "-m", "piper", "-m", str(voice), "-f", str(wav), "--", scene["voz"]]
    )
    dur = max(wav_seconds(wav) + 0.6, float(scene["min_s"]))
    frames = round(dur * FPS)
    out = work / f"{sid}.mp4"
    fade = f"fade=t=in:st=0:d=0.25,fade=t=out:st={dur - 0.25:.2f}:d=0.25"
    audio = f"[1:a]adelay=250|250,apad,atrim=0:{dur:.3f},afade=t=out:st={dur - 0.3:.2f}:d=0.3[a]"
    if scene.get("tipo") == "rotulo":
        card = work / f"{sid}.png"
        title_card(scene, card)
        vf = f"[0:v]scale={W}:{H},format=yuv420p,{fade}[v]"
        inputs = ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(card), "-i", str(wav)]
    else:
        cap = work / f"{sid}_cap.png"
        caption_overlay(scene["subtitulo"], cap)
        zoom = (
            f"[0:v]scale={W * 2}:{H * 2},zoompan=z='min(1+0.06*on/{frames},1.06)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}[z];"
            f"[z][2:v]overlay=0:0,format=yuv420p,{fade}[v]"
        )
        vf = zoom
        inputs = [
            "-loop",
            "1",
            "-t",
            f"{dur:.3f}",
            "-i",
            str(shots / scene["imagen"]),
            "-i",
            str(wav),
            "-loop",
            "1",
            "-t",
            f"{dur:.3f}",
            "-i",
            str(cap),
        ]
    run(
        [
            FF,
            "-y",
            *inputs,
            "-filter_complex",
            f"{vf};{audio}",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            f"{dur:.3f}",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            "4000k",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(out),
        ]
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("escenas")
    ap.add_argument("--shots", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.loads(Path(a.escenas).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        clips = [
            scene_clip(s, Path(a.shots), Path(a.voice), work) for s in spec["escenas"]
        ]
        lst = work / "list.txt"
        lst.write_text("".join(f"file '{c}'\n" for c in clips))
        run(
            [
                FF,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(lst),
                "-c:v",
                "libx264",
                "-b:v",
                "4000k",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                a.out,
            ]
        )
    print(a.out)


if __name__ == "__main__":
    main()
