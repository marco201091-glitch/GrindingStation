"""Build the shared code-native background for GrindingStation."""
from pathlib import Path
from PIL import Image, ImageDraw


def build():
    bg = Image.new("RGB", (600, 1600), "#0B1220")
    draw = ImageDraw.Draw(bg)
    for y in range(1600):
        t = max(0, 1 - y / 700)
        draw.line((0, y, 599, y), fill=(11 + int(4*t), 18 + int(9*t), 32 + int(11*t)))
    bg.save(Path(__file__).resolve().parents[1] / "images" / "station_background.png")


if __name__ == "__main__":
    build()
