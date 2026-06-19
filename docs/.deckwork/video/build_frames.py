#!/usr/bin/env python
"""Build branded 1920x1080 demo-video frames for the IDBI Wealth Copilot."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = "/Users/rahulsingh/Desktop/IDBI Wealth Copilot/docs/screenshots"
OUT = os.path.join(HERE, "frames")
os.makedirs(OUT, exist_ok=True)

W, H = 1920, 1080
BG0, BG1 = (12, 20, 48), (6, 10, 22)
TEAL = (34, 227, 200)
VIOLET = (164, 114, 255)
MAGENTA = (255, 92, 200)
AMBER = (255, 176, 46)
TEXT = (231, 237, 248)
MUTED = (138, 153, 183)
OK = (47, 227, 154)

FONT_DIRS = ["/System/Library/Fonts/Supplemental", "/Library/Fonts", "/System/Library/Fonts"]


def font(names, size):
    for n in names:
        for d in FONT_DIRS:
            p = os.path.join(d, n)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def F(size, bold=False):
    return font(["Arial Bold.ttf" if bold else "Arial.ttf", "Helvetica.ttc"], size)


def GLYPH(size):
    return font(["Arial Unicode.ttf", "Apple Symbols.ttf", "Arial.ttf"], size)


def gradient_bg():
    base = Image.new("RGB", (W, H), BG1)
    top = Image.new("RGB", (W, H), BG0)
    mask = Image.new("L", (W, H))
    md = mask.load()
    for y in range(H):
        v = int(255 * (1 - y / H) ** 1.3)
        for x in range(0, W, 1):
            md[x, y] = v
    base = Image.composite(top, base, mask)
    glow = Image.new("RGB", (W, H), BG1)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-300, -300, 500, 500], fill=(13, 70, 64))
    gd.ellipse([W - 500, H - 500, W + 300, H + 300], fill=(50, 30, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    return Image.blend(base, glow, 0.45)


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_left_panel(d, glyph, color, title, bullets):
    x = 90
    # icon badge
    d.ellipse([x, 150, x + 96, 246], fill=(18, 30, 54), outline=color, width=3)
    g = GLYPH(56)
    gx = x + 48 - d.textlength(glyph, font=g) / 2
    d.text((gx, 168), glyph, font=g, fill=color)
    # title
    tf = F(58, bold=True)
    ty = 290
    for ln in wrap(d, title, tf, 720):
        d.text((x, ty), ln, font=tf, fill=TEXT)
        ty += 70
    ty += 16
    bf = F(31)
    for b in bullets:
        d.ellipse([x + 4, ty + 14, x + 16, ty + 26], fill=color)
        for i, ln in enumerate(wrap(d, b, bf, 660)):
            d.text((x + 34, ty), ln, font=bf, fill=MUTED if i else TEXT)
            ty += 44
        ty += 14


def place_shot(img, path, crop=None):
    shot = Image.open(path).convert("RGB")
    if crop:
        w, h = shot.size
        shot = shot.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    area_x, area_y, area_w, area_h = 880, 90, 960, 900
    sw, sh = shot.size
    scale = min(area_w / sw, area_h / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    shot = shot.resize((nw, nh), Image.LANCZOS)
    px, py = area_x + (area_w - nw) // 2, area_y + (area_h - nh) // 2
    # border frame
    fr = ImageDraw.Draw(img)
    fr.rounded_rectangle([px - 6, py - 6, px + nw + 6, py + nh + 6], radius=14, outline=(60, 80, 120), width=2)
    img.paste(shot, (px, py))


def brand(d):
    d.ellipse([88, 70, 112, 94], fill=None, outline=TEAL, width=0)
    d.ellipse([88, 70, 112, 94], fill=(18, 179, 164))
    d.text((124, 70), "IDBI", font=F(26, bold=True), fill=TEAL)
    d.text((184, 72), "WEALTH COPILOT", font=F(22), fill=MUTED)


def risk_panel(img):
    d = ImageDraw.Draw(img)
    cx, cy, r = 1360, 540, 230
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(40, 55, 80), width=44)
    d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + int(360 * 0.62), fill=VIOLET, width=44)
    d.text((cx - d.textlength("62", font=F(120, bold=True)) / 2, cy - 90), "62", font=F(120, bold=True), fill=VIOLET)
    sub = "/ 100  ·  BALANCED"
    d.text((cx - d.textlength(sub, font=F(30)) / 2, cy + 60), sub, font=F(30), fill=MUTED)


def shield_panel(img):
    d = ImageDraw.Draw(img)
    cx, cy = 1360, 470
    pts = [(cx, cy - 200), (cx + 150, cy - 130), (cx + 150, cy + 40), (cx, cy + 210), (cx - 150, cy + 40), (cx - 150, cy - 130)]
    d.polygon(pts, fill=(24, 36, 60), outline=MAGENTA)
    d.line([(cx - 60, cy), (cx - 15, cy + 55), (cx + 70, cy - 60)], fill=OK, width=14, joint="curve")
    msg = "Never promises guaranteed returns"
    d.text((cx - d.textlength(msg, font=F(30, bold=True)) / 2, cy + 250), msg, font=F(30, bold=True), fill=TEXT)
    sub = "Guardrail enforced in code · unit-tested"
    d.text((cx - d.textlength(sub, font=F(26)) / 2, cy + 296), sub, font=F(26), fill=MUTED)


def title_frame():
    img = gradient_bg()
    d = ImageDraw.Draw(img)
    brand(d)
    d.text((150, 360), "Meet", font=F(64), fill=TEXT)
    d.text((310, 352), "Aanya", font=F(80, bold=True), fill=TEAL)
    d.text((150, 470), "your AI Wealth Copilot", font=F(52), fill=TEXT)
    for i, ln in enumerate([
        "Avatar-led · agentic · explainable wealth advisory, in the IDBI app.",
        "IDBI Innovate 2026  ·  Track 01 — Wealth Advisory",
        "Team Agentic_Hackers  ·  Lead: Gokul D",
    ]):
        d.text((152, 580 + i * 56), ln, font=F(32 if i == 0 else 28), fill=MUTED if i else TEXT)
    return img


def outro_frame():
    img = gradient_bg()
    d = ImageDraw.Draw(img)
    brand(d)
    d.text((150, 360), "A personal wealth manager", font=F(56, bold=True), fill=TEXT)
    d.text((150, 432), "for every customer — at near-zero marginal cost.", font=F(40), fill=TEAL)
    for i, ln in enumerate([
        "Avatar  ·  Voice  ·  Charts  ·  Compliant by design",
        "github.com/Rahulcse79/IDBI-Wealth-Copilot",
        "Thank you — Team Agentic_Hackers",
    ]):
        d.text((152, 560 + i * 60), ln, font=F(34 if i == 0 else 30), fill=MUTED if i == 1 else TEXT)
    return img


SCENES = [
    dict(kind="title"),
    dict(glyph="✦", color=TEAL, title="My snapshot",
         bullets=["Reads your transactions to estimate income, savings rate, idle cash and costly debt.",
                  "Ranks the next best actions — each backed by your own numbers."],
         shot="01-snapshot-charts.png"),
    dict(glyph="◑", color=TEAL, title="Where my money goes",
         bullets=["Your spending as a clear donut, by category.",
                  "Income vs spending vs surplus — understood visually, in seconds."],
         shot="01-snapshot-charts.png", crop=(0.46, 0.40, 0.99, 0.86)),
    dict(glyph="◎", color=VIOLET, title="Plan Rs 50L house",
         bullets=["Computes the exact monthly SIP for your goal.",
                  "Real IDBI product allocation + a projected-growth chart with a live what-if slider."],
         shot="02-goal-plan.png"),
    dict(glyph="◷", color=VIOLET, title="Retirement plan",
         bullets=["The same engine plans Rs 2 crore over 20 years, instantly.",
                  "Every figure computed, not guessed — shown as a chart you can trust."],
         shot="02-goal-plan.png", crop=(0.46, 0.55, 0.99, 0.97)),
    dict(kind="risk", glyph="◭", color=VIOLET, title="My risk profile",
         bullets=["Scores your risk capacity from 0 to 100.",
                  "Explained factor by factor — the explainability a bank and a regulator need."]),
    dict(glyph="★", color=AMBER, title="Best products",
         bullets=["Searches the IDBI catalogue and recommends only real products.",
                  "Indicative — never guaranteed — returns, compared side by side."],
         shot="03-products.png"),
    dict(kind="safe", glyph="✓", color=MAGENTA, title="Are you safe?",
         bullets=["Ask her to guarantee returns — she refuses.",
                  "A code-level guardrail blocks guaranteed-return claims and any ungrounded product."]),
    dict(kind="outro"),
]


def main():
    for i, sc in enumerate(SCENES, 1):
        kind = sc.get("kind", "shot")
        if kind == "title":
            img = title_frame()
        elif kind == "outro":
            img = outro_frame()
        else:
            img = gradient_bg()
            d = ImageDraw.Draw(img)
            brand(d)
            draw_left_panel(d, sc["glyph"], sc["color"], sc["title"], sc["bullets"])
            if kind == "risk":
                risk_panel(img)
            elif kind == "safe":
                shield_panel(img)
            else:
                place_shot(img, os.path.join(SHOTS, sc["shot"]), sc.get("crop"))
        img.save(os.path.join(OUT, f"{i:02d}.png"))
        print("frame", i, kind)


if __name__ == "__main__":
    main()
