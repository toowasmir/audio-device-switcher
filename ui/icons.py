from PIL import Image, ImageDraw
import os

def create_audio_icon(size: int = 64) -> Image.Image:
    """
    Generates a sleek, anti-aliased speaker/sound icon suitable for Windows system tray
    and application windows.
    """
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Accent colors (Fluent modern cyan & white)
    accent_color = (76, 194, 255, 255) # Windows 11 Cyan
    white_color = (255, 255, 255, 255)

    # Coordinates scaled
    cx = canvas_size // 2
    cy = canvas_size // 2

    # Draw speaker body:
    # Small rectangle on left
    rx0, ry0 = int(canvas_size * 0.16), int(canvas_size * 0.38)
    rx1, ry1 = int(canvas_size * 0.35), int(canvas_size * 0.62)
    draw.rectangle([rx0, ry0, rx1, ry1], fill=white_color)

    # Cone polygon connecting to rectangle
    cone_points = [
        (rx1, ry0),
        (int(canvas_size * 0.54), int(canvas_size * 0.22)),
        (int(canvas_size * 0.54), int(canvas_size * 0.78)),
        (rx1, ry1)
    ]
    draw.polygon(cone_points, fill=white_color)

    # Draw sound waves on the right
    stroke_w = int(canvas_size * 0.05)

    # Wave 1 (inner)
    w1_box = [
        int(canvas_size * 0.45),
        int(canvas_size * 0.32),
        int(canvas_size * 0.72),
        int(canvas_size * 0.68)
    ]
    draw.arc(w1_box, start=305, end=55, fill=accent_color, width=stroke_w)

    # Wave 2 (outer)
    w2_box = [
        int(canvas_size * 0.40),
        int(canvas_size * 0.18),
        int(canvas_size * 0.90),
        int(canvas_size * 0.82)
    ]
    draw.arc(w2_box, start=315, end=45, fill=accent_color, width=stroke_w)

    # Downsample with Lanczos for smooth anti-aliased look
    return img.resize((size, size), Image.Resampling.LANCZOS)


def ensure_ico_file(ico_path: str):
    """Generates and saves a multi-resolution .ico file if not already present."""
    if not os.path.exists(ico_path):
        sizes = [16, 32, 48, 64, 128, 256]
        images = [create_audio_icon(s) for s in sizes]
        images[0].save(
            ico_path,
            format="ICO",
            sizes=[(s, s) for s in sizes],
            append_images=images[1:]
        )
