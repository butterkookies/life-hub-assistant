"""Generate PWA icons for Andrei's Life Hub Assistant."""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_icons():
    icons_dir = Path("web/public/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    sizes = {
        "icon-192.png": (192, 192, False),
        "icon-512.png": (512, 512, False),
        "icon-maskable-512.png": (512, 512, True),
        "apple-touch-icon.png": (180, 180, False),
    }

    # Brand Colors:
    # Canvas: #fbfbfa
    # Blue: #0075de
    # Accent: #191919
    for filename, (w, h, maskable) in sizes.items():
        img = Image.new("RGBA", (w, h), (251, 251, 250, 255))
        draw = ImageDraw.Draw(img)

        margin = int(w * 0.1) if not maskable else int(w * 0.18)
        radius = int(w * 0.22) if not maskable else 0

        # Card container
        rect_x0, rect_y0 = margin, margin
        rect_x1, rect_y1 = w - margin, h - margin

        if not maskable:
            # Draw rounded background badge
            draw.rounded_rectangle(
                [rect_x0, rect_y0, rect_x1, rect_y1],
                radius=radius,
                fill=(255, 255, 255, 255),
                outline=(233, 233, 232, 255),
                width=max(2, int(w * 0.015))
            )

        # Draw Notion-inspired minimalist stylized glyph:
        # A sleek blue cube/sparkle motif
        cx, cy = w / 2, h / 2
        glyph_size = int(w * (0.28 if maskable else 0.32))

        # Main blue pillar
        p_w = int(glyph_size * 0.28)
        p_h = int(glyph_size * 1.2)
        p_x0 = int(cx - glyph_size * 0.6)
        p_y0 = int(cy - p_h / 2)
        draw.rounded_rectangle(
            [p_x0, p_y0, p_x0 + p_w, p_y0 + p_h],
            radius=int(p_w * 0.4),
            fill=(0, 117, 222, 255)  # Notion Blue
        )

        # Second blue pillar
        p2_x0 = int(cx + glyph_size * 0.6 - p_w)
        draw.rounded_rectangle(
            [p2_x0, p_y0, p2_x0 + p_w, p_y0 + p_h],
            radius=int(p_w * 0.4),
            fill=(0, 117, 222, 255)
        )

        # Crossbar connecting them (H for Hub)
        bar_h = int(p_w * 0.9)
        draw.rounded_rectangle(
            [p_x0 + p_w // 2, int(cy - bar_h / 2), p2_x0 + p_w // 2, int(cy + bar_h / 2)],
            radius=int(bar_h * 0.3),
            fill=(25, 25, 25, 255)  # Notion Dark Charcoal
        )

        # Accent sparkle dot in top right
        dot_r = int(w * 0.04)
        dot_cx = int(p2_x0 + p_w / 2)
        dot_cy = int(p_y0 - dot_r * 1.5)
        draw.ellipse(
            [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
            fill=(217, 115, 13, 255)  # Notion Warm Amber
        )

        out_path = icons_dir / filename
        img.save(out_path, "PNG")
        print(f"Generated {out_path} ({w}x{h})")

if __name__ == "__main__":
    generate_icons()
