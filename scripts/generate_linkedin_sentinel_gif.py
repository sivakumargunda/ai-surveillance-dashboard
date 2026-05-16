from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "sentinel_linkedin_post_template.gif"
WIDTH = 1080
HEIGHT = 1080
FPS = 12
SECONDS = 8
FRAMES = FPS * SECONDS


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


FONT_HERO = font(72, True)
FONT_SUB = font(34)
FONT_BODY = font(30)
FONT_SMALL = font(24)
FONT_TINY = font(18)
FONT_BADGE = font(22, True)
FONT_METRIC = font(42, True)


def lerp(a: float, b: float, t: float) -> int:
    return int(a + (b - a) * t)


def ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, t)))


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_fit(draw: ImageDraw.ImageDraw, xy, text, font_obj, fill, max_width):
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    x, y = xy
    line_height = int(font_obj.size * 1.22)
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += line_height
    return y


def gradient_background(frame: int) -> Image.Image:
    small_w, small_h = 180, 180
    img = Image.new("RGB", (small_w, small_h), "#07110f")
    px = img.load()
    pulse = (math.sin(frame / FRAMES * math.tau) + 1) / 2
    for y in range(small_h):
        yr = y / (small_h - 1)
        for x in range(small_w):
            xr = x / (small_w - 1)
            vignette = 1 - min(0.65, math.hypot(xr - 0.48, yr - 0.46))
            r = lerp(5, 18, yr) + int(10 * pulse * (1 - yr))
            g = lerp(17, 44, yr) + int(18 * xr)
            b = lerp(17, 38, xr) + int(10 * (1 - yr))
            px[x, y] = (int(r * vignette), int(g * vignette), int(b * vignette))
    return img.resize((WIDTH, HEIGHT), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(0.35))


def draw_grid(draw: ImageDraw.ImageDraw, frame: int):
    offset = (frame * 5) % 80
    for x in range(-80 + offset, WIDTH, 80):
        draw.line((x, 0, x, HEIGHT), fill=(29, 88, 80), width=1)
    for y in range(-80 + offset, HEIGHT, 80):
        draw.line((0, y, WIDTH, y), fill=(29, 88, 80), width=1)


def draw_camera_panel(draw: ImageDraw.ImageDraw, frame: int):
    panel = (74, 284, 1006, 790)
    rounded(draw, panel, 18, (10, 24, 24), (80, 209, 184), 2)
    draw.rectangle((92, 340, 988, 772), fill=(14, 29, 30))

    # Synthetic camera-feed silhouettes and floor perspective.
    horizon = 522
    for i in range(8):
        y = horizon + i * 34
        draw.line((106, y, 974, y), fill=(24, 57, 55), width=1)
    for i in range(10):
        x = 110 + i * 96
        draw.line((x, 772, 520, horizon), fill=(21, 54, 52), width=1)

    people = [
        (250, 610, 1.0, "#48d6c2"),
        (420, 578, 0.86, "#e8c85c"),
        (645, 632, 1.12, "#48d6c2"),
        (810, 590, 0.92, "#f16d6d"),
    ]
    for idx, (base_x, base_y, scale, color) in enumerate(people):
        bob = math.sin(frame * 0.28 + idx) * 8
        x = base_x + math.sin(frame * 0.11 + idx * 1.7) * 18
        y = base_y + bob
        h = 96 * scale
        w = 42 * scale
        draw.ellipse((x - 16 * scale, y - h, x + 16 * scale, y - h + 32 * scale), fill=(45, 64, 64))
        draw.rounded_rectangle((x - w / 2, y - h + 32 * scale, x + w / 2, y), radius=14, fill=(37, 56, 55))
        if idx in (0, 3):
            margin = 16 + math.sin(frame * 0.22) * 5
            draw.rounded_rectangle(
                (x - w / 2 - margin, y - h - margin, x + w / 2 + margin, y + margin),
                radius=10,
                outline=color,
                width=4,
            )
            draw.text((x - w / 2 - margin, y - h - margin - 28), "TRACKING", font=FONT_TINY, fill=color)

    zone_alpha = (math.sin(frame * 0.2) + 1) / 2
    zone_color = (255, 92, 92) if zone_alpha > 0.45 else (80, 209, 184)
    draw.line((704, 374, 952, 442, 944, 738, 650, 712, 704, 374), fill=zone_color, width=5)
    draw.text((724, 392), "RESTRICTED ZONE", font=FONT_SMALL, fill=zone_color)

    scan_y = 354 + (frame * 9 % 390)
    draw.line((98, scan_y, 982, scan_y), fill=(77, 232, 205), width=3)

    draw.text((100, 304), "LIVE CAMERA 03", font=FONT_BADGE, fill=(222, 250, 244))
    draw.text((820, 304), "AI ACTIVE", font=FONT_BADGE, fill=(77, 232, 205))


def scene_for_frame(frame: int):
    scenes = [
        ("Retail theft prevention", "45% loss reduction", "Zone alerts + crowd detection"),
        ("Banking access control", "$1M+ risk avoided", "Restricted-area intelligence"),
        ("Healthcare protection", "60% fewer theft events", "Audit trails for sensitive rooms"),
        ("Workplace safety", "40% fewer incidents", "Hazard-zone monitoring"),
    ]
    scene_len = FRAMES / len(scenes)
    idx = min(len(scenes) - 1, int(frame // scene_len))
    local = (frame - idx * scene_len) / scene_len
    return scenes[idx], ease(min(local * 1.5, 1)), ease(max(0, (local - 0.78) / 0.22))


def draw_frame(frame: int) -> Image.Image:
    img = gradient_background(frame).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    draw_grid(draw, frame)

    draw.text((74, 58), "Sentinel AI", font=FONT_HERO, fill=(235, 255, 250))
    draw.text((78, 142), "Transform CCTV into operational intelligence", font=FONT_SUB, fill=(159, 206, 196))

    draw_camera_panel(draw, frame)

    (title, metric, detail), fade_in, fade_out = scene_for_frame(frame)
    alpha = int(255 * fade_in * (1 - 0.6 * fade_out))
    card_y = int(824 + 18 * (1 - fade_in))
    rounded(draw, (74, card_y, 1006, 988), 18, (9, 22, 22, 232), (65, 165, 151, 190), 2)
    draw.text((112, card_y + 28), title.upper(), font=FONT_BADGE, fill=(118, 232, 209, alpha))
    draw.text((112, card_y + 62), metric, font=FONT_METRIC, fill=(246, 248, 236, alpha))
    draw.text((112, card_y + 118), detail, font=FONT_BODY, fill=(181, 217, 210, alpha))

    # Bottom CTA strip.
    rounded(draw, (704, 916, 966, 966), 14, (70, 232, 204, 245))
    draw.text((738, 928), "Request a demo", font=FONT_BADGE, fill=(3, 22, 20))

    # Tiny rotating proof points.
    tick = ["Real-time alerts", "Automated logs", "Faster response"][frame // 16 % 3]
    draw.text((78, 1010), tick, font=FONT_SMALL, fill=(129, 180, 171))
    draw.text((650, 1014), "#AI #ComputerVision #SecurityTech", font=FONT_TINY, fill=(129, 180, 171))

    return img.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [draw_frame(i) for i in range(FRAMES)]
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=int(1000 / FPS),
        loop=0,
        disposal=2,
    )
    print(OUT)


if __name__ == "__main__":
    main()
