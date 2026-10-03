#!/usr/bin/env python3
"""Generate 52 pixel-art playing cards in Naruto × Minecraft style."""
from PIL import Image, ImageDraw, ImageFont
import os, random

OUT = os.path.join(os.path.dirname(__file__), 'cards')
os.makedirs(OUT, exist_ok=True)

# Card sizing — pixel-art: each card = grid of 16x22 cells, 16px each = 256x352
CELL = 18
W, H = 16 * CELL, 22 * CELL  # 288 x 396

# Naruto × Minecraft palette
PARCHMENT = (245, 233, 196)   # warm cream
PARCHMENT_D = (201, 165, 137)
BORDER = (90, 50, 25)          # dark dirt
LEAF_GREEN = (92, 184, 92)     # Konoha grass
LEAF_DARK = (46, 110, 46)
ORANGE = (255, 140, 26)        # Naruto jumpsuit
ORANGE_D = (204, 106, 0)
RED = (192, 42, 42)
RED_D = (138, 26, 26)
BLACK = (26, 26, 26)
WHITE = (250, 250, 245)
SHADOW = (0, 0, 0, 80)

RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
SUITS = [('♠', 'spade', BLACK, 'black'),
         ('♥', 'heart', RED, 'red'),
         ('♦', 'diamond', ORANGE, 'black'),
         ('♣', 'club', LEAF_GREEN, 'black')]

# Fonts — try to load something monospace-ish
def load_font(size):
    paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf',
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F_RANK = load_font(int(CELL * 1.6))
F_RANK_SMALL = load_font(int(CELL * 1.1))
F_SUIT_BIG = load_font(int(CELL * 6))
F_SUIT_CENTER = load_font(int(CELL * 4))
F_HIDDEN = load_font(int(CELL * 1.4))

def pixel_rect(d, x, y, w, h, color):
    d.rectangle([x, y, x+w-1, y+h-1], fill=color)

def draw_konoha_leaf(d, cx, cy, size, color):
    """Draw a stylized Konoha leaf at (cx, cy) with given pixel size."""
    # Teardrop leaf shape via pixel approximation
    s = size
    # Outline first
    leaf_pts = []
    for i in range(12):
        t = i / 11
        # Leaf outline (teardrop)
        px = cx + int((t * 2 - 1) * s)
        py = cy + int((0.5 - abs(t - 0.5)) * 2 * s - s * 0.3)
        leaf_pts.append((px, py))
    # Stem
    d.line([(cx, cy + size*1.1), (cx, cy + size*1.8)], fill=color, width=max(2, s//8))
    # Filled leaf body — render as ellipse-ish via multiple horizontal slices
    for i in range(s*2):
        yy = cy - s + i
        # width at this y
        rel = (yy - (cy - s)) / (2 * s)  # 0..1
        if 0 <= rel <= 1:
            w_here = int((1 - abs(2*rel - 1)) ** 0.6 * s * 1.1)
            d.rectangle([cx - w_here//2, yy, cx + w_here//2, yy], fill=color)

def make_card_image(rank, suit_symbol, suit_name, color_main, color_class):
    img = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)

    # Card body — parchment with dirt border (3px)
    border = 4
    pixel_rect(d, 0, 0, W, H, BORDER)
    pixel_rect(d, border, border, W-2*border, H-2*border, PARCHMENT)
    # Inner darker frame
    pixel_rect(d, border*2, border*2, W-4*border, H-4*border, PARCHMENT)

    # Suit color for rank text
    if suit_name == 'heart' or suit_name == 'diamond':
        rank_color = RED
    elif suit_name == 'spade' or suit_name == 'club':
        rank_color = BLACK
    else:
        rank_color = color_main

    # Top-left rank + suit
    rank_str = rank
    d.text((border*3 + 2, border*3 + 2), rank_str, fill=rank_color, font=F_RANK)
    d.text((border*3 + 2, border*3 + 2 + int(CELL*1.7)), suit_symbol, fill=rank_color, font=F_RANK_SMALL)

    # Bottom-right rank + suit (rotated 180 via flip)
    rb_img = Image.new('RGBA', (int(CELL*3), int(CELL*4)), (0,0,0,0))
    rbd = ImageDraw.Draw(rb_img)
    rbd.text((2, 2), rank_str, fill=rank_color, font=F_RANK)
    rbd.text((2, 2 + int(CELL*1.7)), suit_symbol, fill=rank_color, font=F_RANK_SMALL)
    rb_img = rb_img.rotate(180)
    img.paste(rb_img, (W - int(CELL*3) - border*3 - 2, H - int(CELL*4) - border*3 - 2), rb_img)

    # Center: 1 big symbol + Konoha leaf watermark
    cx, cy = W // 2, H // 2

    # Light Konoha watermark behind
    wm = Image.new('RGBA', (W, H), (0,0,0,0))
    wmd = ImageDraw.Draw(wm)
    draw_konoha_leaf(wmd, cx, cy, int(CELL*2.5), (200, 165, 110, 70))
    img.paste(wm, (0, 0), wm)

    # Big suit symbol
    bbox = d.textbbox((0, 0), suit_symbol, font=F_SUIT_BIG)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text((cx - tw//2 - bbox[0], cy - th//2 - bbox[1] - CELL//2), suit_symbol, fill=rank_color, font=F_SUIT_BIG)

    # Pip layout for number cards (2-10): arrange suit_symbols in classic pattern
    if rank not in ('A', 'J', 'Q', 'K'):
        n = int(rank)
        positions = PIP_LAYOUTS[n]  # list of (x_pct, y_pct)
        for (xp, yp) in positions:
            px = int(xp * W)
            py = int(yp * H)
            sbbox = F_SUIT_CENTER.getbbox(suit_symbol)
            sw = sbbox[2] - sbbox[0]
            sh = sbbox[3] - sbbox[1]
            d.text((px - sw//2 - sbbox[0], py - sh//2 - sbbox[1]), suit_symbol, fill=rank_color, font=F_SUIT_CENTER)

    # For face cards (J, Q, K): big Konoha leaf instead of face portrait
    if rank in ('J', 'Q', 'K'):
        # Cover center with a Konoha emblem
        size_px = int(CELL * 4)
        overlay = Image.new('RGBA', (size_px*2, size_px*2), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        # Konoha swirl: 3 comma shapes around a center
        for ang in (0, 120, 240):
            import math
            rad = math.radians(ang)
            ox = size_px + math.cos(rad) * size_px*0.45
            oy = size_px + math.sin(rad) * size_px*0.45
            draw_konoha_leaf(od, int(ox), int(oy), int(CELL*1.4), LEAF_DARK)
        # Center
        draw_konoha_leaf(od, size_px, size_px, int(CELL*1.0), LEAF_GREEN)
        img.paste(overlay, (cx - size_px, cy - size_px - CELL//2), overlay)
        # Label below
        labels = {'J': 'ГЕНИН', 'Q': 'ЧУНИН', 'K': 'КАГЕ'}
        d.text((cx - CELL*1.5, cy + CELL*3.2), labels[rank], fill=ORANGE_D, font=F_RANK_SMALL)

    # For Ace: single big leaf behind the suit
    if rank == 'A':
        size_px = int(CELL * 5)
        overlay = Image.new('RGBA', (size_px*2, size_px*2), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        draw_konoha_leaf(od, size_px, size_px, int(CELL*1.8), LEAF_DARK)
        draw_konoha_leaf(od, size_px, size_px, int(CELL*1.2), LEAF_GREEN)
        img.paste(overlay, (cx - size_px, cy - size_px - CELL//2), overlay)

    return img

def make_card_back():
    img = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    border = 4
    pixel_rect(d, 0, 0, W, H, BORDER)
    pixel_rect(d, border, border, W-2*border, H-2*border, (30, 50, 35))
    # Diagonal cross-hatch
    for i in range(-H, W, CELL//2):
        d.line([(i, 0), (i + H, H)], fill=(46, 110, 46), width=2)
    # Big Konoha leaf
    cx, cy = W//2, H//2
    draw_konoha_leaf(d, cx, cy, int(CELL*3.5), LEAF_GREEN)
    draw_konoha_leaf(d, cx, cy, int(CELL*2.3), (164, 255, 138))
    # "LIGHT GAMES" text band
    band_y = H - int(CELL*2.5)
    d.rectangle([border*3, band_y, W-border*3, band_y + int(CELL*1.4)], fill=ORANGE_D)
    d.text((cx - CELL*3, band_y + CELL//4), '🍃 LIGHT', fill=PARCHMENT, font=F_HIDDEN)
    return img

# Standard pip layouts (x_pct, y_pct) — based on classic Bicycle deck
PIP_LAYOUTS = {
    2: [(0.5, 0.30), (0.5, 0.70)],
    3: [(0.5, 0.25), (0.5, 0.50), (0.5, 0.75)],
    4: [(0.30, 0.28), (0.70, 0.28), (0.30, 0.72), (0.70, 0.72)],
    5: [(0.30, 0.28), (0.70, 0.28), (0.5, 0.50), (0.30, 0.72), (0.70, 0.72)],
    6: [(0.30, 0.28), (0.70, 0.28), (0.30, 0.50), (0.70, 0.50), (0.30, 0.72), (0.70, 0.72)],
    7: [(0.30, 0.28), (0.70, 0.28), (0.30, 0.50), (0.70, 0.50), (0.30, 0.72), (0.70, 0.72), (0.5, 0.39)],
    8: [(0.30, 0.28), (0.70, 0.28), (0.30, 0.50), (0.70, 0.50), (0.30, 0.72), (0.70, 0.72), (0.5, 0.39), (0.5, 0.61)],
    9: [(0.30, 0.28), (0.70, 0.28), (0.30, 0.45), (0.70, 0.45), (0.5, 0.50), (0.30, 0.55), (0.70, 0.55), (0.30, 0.72), (0.70, 0.72)],
    10: [(0.30, 0.25), (0.70, 0.25), (0.30, 0.42), (0.70, 0.42), (0.5, 0.34), (0.5, 0.50), (0.5, 0.66), (0.30, 0.58), (0.70, 0.58), (0.30, 0.75), (0.70, 0.75)],
}

# Generate all 52
count = 0
for rank in RANKS:
    for (symbol, name, c_main, c_class) in SUITS:
        img = make_card_image(rank, symbol, name, c_main, c_class)
        fname = f'{rank}_{name}.png'
        img.save(os.path.join(OUT, fname))
        count += 1
back = make_card_back()
back.save(os.path.join(OUT, 'back.png'))
print(f'Generated {count} cards + 1 back in {OUT}')