"""Build a simple orange play-button icon for the desktop app."""

from pathlib import Path

from PIL import Image, ImageDraw


def draw(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pad = max(1, round(size * 0.04))
    radius = max(2, round(size * 0.22))
    pen.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=radius,
        fill=(255, 122, 69, 255),
    )
    cx = size * 0.56
    cy = size * 0.50
    reach = size * 0.24
    pen.polygon(
        [
            (cx - reach * 0.72, cy - reach),
            (cx - reach * 0.72, cy + reach),
            (cx + reach, cy),
        ],
        fill=(26, 13, 7, 255),
    )
    return image


def main() -> None:
    folder = Path(__file__).resolve().parent / "assets"
    folder.mkdir(exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw(size) for size in sizes]
    images[-1].save(
        folder / "app.ico",
        format="ICO",
        sizes=[(size, size) for size in sizes],
        append_images=images[:-1],
    )
    images[-1].save(folder / "app.png", format="PNG")


if __name__ == "__main__":
    main()
