#!/usr/bin/env python3
"""ai-excited-01 entry: a giant glowing jellyfish drifts over a tiny neon city.

Original procedural art, stdlib only (struct + zlib + math + os).
Fully deterministic: fixed integer seeds, no time, no OS randomness,
no network, no external assets. Writes exactly one 1024x1024 PNG to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Concept: scale twist -- a jellyfish the size of a skyscraper floats over
a miniature neon city at night. Cyan/magenta glow against a dark indigo
sky, warm yellow windows below. One dominant shape (the bell) that still
reads clearly when shrunk to ~300px.
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- helpers

def clamp(v):
    if v < 0:
        return 0
    if v > 255:
        return 255
    return int(v)


def lerp(a, b, t):
    return a + (b - a) * t


def mix3(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def _lcg(state):
    """Deterministic pseudo-random stream (glibc-style LCG)."""
    return (1103515245 * state + 12345) & 0x7FFFFFFF


def _hash2(a, b):
    """Deterministic 0..1 hash of two integers."""
    h = (a * 73856093) ^ (b * 19349663)
    h ^= (h >> 13)
    h = (h * 83492791) & 0xFFFFFFFF
    h ^= (h >> 16)
    return (h & 0xFFFFFFFF) / 4294967296.0


# ---------------------------------------------------------------- pixel ops

def add_px(buf, x, y, r, g, b):
    """Additive blend of one pixel, clamped."""
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = clamp(buf[i] + r)
        buf[i + 1] = clamp(buf[i + 1] + g)
        buf[i + 2] = clamp(buf[i + 2] + b)


def fill_rect(buf, x0, y0, x1, y1, col):
    """Fast solid rectangle fill (clipped)."""
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x0 >= x1 or y0 >= y1:
        return
    r, g, b = col
    row = bytes((r, g, b)) * (x1 - x0)
    for y in range(y0, y1):
        s = y * W * 3 + x0 * 3
        buf[s:s + len(row)] = row


def add_disc(buf, cx, cy, rad, col, strength=1.0):
    """Soft additive glowing disc (radial falloff)."""
    r0 = int(rad)
    for dy in range(-r0, r0 + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        half = int(math.sqrt(max(0, r0 * r0 - dy * dy)))
        for dx in range(-half, half + 1):
            d = math.sqrt(dx * dx + dy * dy) / rad
            f = (1.0 - d * d) * strength
            if f <= 0:
                continue
            add_px(buf, cx + dx, y, col[0] * f, col[1] * f, col[2] * f)


# ---------------------------------------------------------------- scene

def paint_sky(buf):
    """Indigo night gradient, darker at top, warmer toward the horizon."""
    top = (7, 5, 32)
    mid = (24, 11, 62)
    hor = (56, 20, 96)
    for y in range(H):
        t = y / (H - 1)
        if t < 0.55:
            c = mix3(top, mid, t / 0.55)
        else:
            c = mix3(mid, hor, (t - 0.55) / 0.45)
        row = bytes((clamp(c[0]), clamp(c[1]), clamp(c[2]))) * W
        s = y * W * 3
        buf[s:s + len(row)] = row


def paint_stars(buf):
    """Deterministic stars: bright core + cross sparkle, a few big ones."""
    state = 987654321
    for _ in range(260):
        state = _lcg(state)
        x = state % W
        state = _lcg(state)
        y = state % 640  # stars only in the sky, above the city
        state = _lcg(state)
        bright = 90 + (state % 166)
        state = _lcg(state)
        big = (state % 17) == 0
        add_px(buf, x, y, bright, bright, bright)
        add_px(buf, x - 1, y, bright * 0.35, bright * 0.35, bright * 0.4)
        add_px(buf, x + 1, y, bright * 0.35, bright * 0.35, bright * 0.4)
        add_px(buf, x, y - 1, bright * 0.35, bright * 0.35, bright * 0.4)
        add_px(buf, x, y + 1, bright * 0.35, bright * 0.35, bright * 0.4)
        if big:
            for d in (2, 3):
                add_px(buf, x - d, y, bright * 0.22, bright * 0.22, bright * 0.25)
                add_px(buf, x + d, y, bright * 0.22, bright * 0.22, bright * 0.25)
                add_px(buf, x, y - d, bright * 0.22, bright * 0.22, bright * 0.25)
                add_px(buf, x, y + d, bright * 0.22, bright * 0.22, bright * 0.25)


def paint_city(buf):
    """Two silhouette layers + warm lit windows + antenna lights."""
    # Far layer: taller, hazier purple silhouettes.
    state = 424242
    x = -20
    far = []
    while x < W + 20:
        state = _lcg(state)
        w = 46 + (state % 66)
        state = _lcg(state)
        h = 190 + (state % 190)
        far.append((x, w, h))
        x += w + 6
    for (bx, w, h) in far:
        fill_rect(buf, bx, H - h - 60, bx + w, H, (26, 16, 58))

    # Near layer: dark silhouettes with lit windows.
    state = 777001
    x = -10
    near = []
    while x < W + 10:
        state = _lcg(state)
        w = 52 + (state % 78)
        state = _lcg(state)
        h = 120 + (state % 230)
        near.append((x, w, h))
        x += w + 4
    for (bx, w, h) in near:
        top = H - h
        shade = 10 + int(_hash2(bx, h) * 8)
        fill_rect(buf, bx, top, bx + w, H, (shade, shade - 2, shade + 10))
        # Roof antenna on some buildings.
        if _hash2(bx, 7) < 0.4:
            ax = bx + w // 2
            fill_rect(buf, ax, top - 22, ax + 2, top, (shade + 6, shade + 4, shade + 12))
            add_px(buf, ax, top - 24, 255, 60, 60)
            add_px(buf, ax + 1, top - 24, 255, 60, 60)
        # Windows: warm yellow, a few cyan.
        cols = max(1, (w - 10) // 16)
        rows = max(1, (h - 14) // 20)
        for cy in range(rows):
            wy = top + 8 + cy * 20
            for cx in range(cols):
                wx = bx + 6 + cx * 16
                r = _hash2(bx + cx * 31, wy)
                if r < 0.52:
                    if r < 0.07:
                        col = (110, 215, 255)  # rare cyan window
                    else:
                        warm = 200 + int(_hash2(wx, wy) * 55)
                        col = (255, warm, 95)
                    fill_rect(buf, wx, wy, wx + 8, wy + 10, col)
    # Street band: dark road with two neon streaks.
    fill_rect(buf, 0, 992, W, H, (8, 6, 20))
    fill_rect(buf, 0, 996, W, 998, (40, 200, 220))
    fill_rect(buf, 0, 1006, W, 1008, (220, 60, 190))


def paint_city_glow(buf):
    """Soft cyan glow the jellyfish casts onto the rooftops below it."""
    for y in range(700, 992):
        ey = (y - 850) / 150.0
        ey2 = ey * ey
        if ey2 >= 1.0:
            continue
        for x in range(240, 785):
            ex = (x - 512) / 272.0
            e2 = ex * ex + ey2
            if e2 >= 1.0:
                continue
            f = (1.0 - e2) * 26.0
            add_px(buf, x, y, 10 * f / 26.0 * 1.6, f * 0.85, f)


# Jellyfish geometry: bell centred (512, 330), radii (290, 225).
JCX, JCY, JRX, JRY = 512, 330, 290, 225


def paint_jellyfish(buf):
    """Bell with radial cyan->magenta gradient, scalloped rim, halo, then
    flowing sine tentacles with glowing orbs."""
    # --- halo + bell: one pass over the bounding ellipse (r <= 1.6) ---
    x0 = max(0, JCX - int(JRX * 1.6))
    x1 = min(W, JCX + int(JRX * 1.6))
    y0 = max(0, JCY - int(JRY * 1.6))
    y1 = min(H, JCY + int(JRY * 1.6))
    inv_rx = 1.0 / JRX
    inv_ry = 1.0 / JRY
    core = (255, 255, 255)
    cyan = (64, 228, 255)
    mag = (255, 64, 198)
    rimc = (148, 38, 158)
    for y in range(y0, y1):
        ny = (y - JCY) * inv_ry
        ny2 = ny * ny
        if ny2 > 2.56:
            continue
        # x extent of the r <= 1.6 ellipse on this row
        dx_max = JRX * math.sqrt(max(0.0, 2.56 - ny2))
        xa = max(x0, int(JCX - dx_max))
        xb = min(x1, int(JCX + dx_max))
        for x in range(xa, xb):
            nx = (x - JCX) * inv_rx
            r2 = nx * nx + ny2
            if r2 > 2.56:
                continue
            i = (y * W + x) * 3
            if r2 <= 1.0:
                # Inside the bell. Upper rim is a clean ellipse; only the
                # lower rim is wavy (bell fringe) so no notches appear.
                r = math.sqrt(r2)
                theta = math.atan2(ny, nx)
                if ny > 0.0:
                    bottom = 0.30 + 0.05 * math.sin(13.0 * theta + 0.7)
                    if ny > bottom:
                        continue  # wavy lower rim / flat-ish underside
                # Radial colour: white core -> cyan -> magenta -> deep rim.
                if r < 0.18:
                    c = mix3(core, cyan, r / 0.18)
                elif r < 0.55:
                    c = mix3(cyan, mag, (r - 0.18) / 0.37 * 0.55)
                elif r < 0.88:
                    c = mix3(cyan, mag, 0.55 + (r - 0.55) / 0.33 * 0.45)
                else:
                    c = mix3(mag, rimc, (r - 0.88) / 0.12)
                # Top light + faint radial rings; angular streaks fade in
                # only away from the centre (avoids a starburst artefact).
                bright = (1.0 - 0.18 * ny) * (0.97 + 0.03 * math.sin(r * 30.0 + 1.0))
                if r > 0.25:
                    streak = min(1.0, (r - 0.25) / 0.25)
                    bright *= 0.97 + 0.03 * math.sin(theta * 14.0) * streak
                buf[i] = clamp(c[0] * bright)
                buf[i + 1] = clamp(c[1] * bright)
                buf[i + 2] = clamp(c[2] * bright)
            else:
                # Halo outside the bell: cyan above, magenta below.
                g = (2.56 - r2) / 1.56
                g = g * g * 62.0
                t = 0.5 + 0.5 * max(-1.0, min(1.0, ny))
                cr = lerp(36, 255, t)
                cg = lerp(190, 60, t)
                cb = lerp(255, 190, t)
                buf[i] = clamp(buf[i] + cr * g / 62.0 * 0.9)
                buf[i + 1] = clamp(buf[i + 1] + cg * g / 62.0 * 0.9)
                buf[i + 2] = clamp(buf[i + 2] + cb * g / 62.0 * 0.9)

    # --- tentacles: sine curves flowing down from the bell rim ---
    tentacles = [
        # (x0, amp, freq, phase, length, thick, colour)
        (268, 26, 0.0110, 0.0, 560, 7, (64, 228, 255)),
        (322, 34, 0.0130, 1.4, 620, 8, (255, 64, 198)),
        (378, 22, 0.0095, 2.6, 540, 6, (170, 100, 255)),
        (436, 30, 0.0120, 0.6, 650, 8, (64, 228, 255)),
        (512, 20, 0.0100, 3.1, 600, 9, (255, 64, 198)),
        (588, 32, 0.0125, 1.9, 640, 8, (64, 228, 255)),
        (646, 24, 0.0090, 4.2, 560, 6, (170, 100, 255)),
        (702, 30, 0.0135, 0.9, 610, 7, (255, 64, 198)),
        (756, 22, 0.0115, 2.2, 520, 6, (64, 228, 255)),
    ]
    y_start = JCY + 62  # just under the bell's flat bottom
    for (tx0, amp, freq, phase, length, thick, col) in tentacles:
        y_end = min(985, y_start + length)
        for y in range(y_start, y_end):
            dy = y - y_start
            prog = dy / max(1, y_end - y_start)
            cx = tx0 + amp * math.sin(y * freq + phase) \
                + 0.45 * amp * math.sin(y * freq * 2.7 + phase * 2.0)
            hw = max(1, int(thick * (1.0 - prog * 0.6)))
            for dx in range(-hw, hw + 1):
                fall = 1.0 - (dx / hw) ** 2
                add_px(buf, int(cx) + dx, y,
                       col[0] * fall * 0.95, col[1] * fall * 0.95,
                       col[2] * fall * 0.95)
        # Glowing orbs riding the tentacle.
        for k in range(1, 5):
            oy = y_start + int(length * k / 5.0)
            if oy >= 985:
                continue
            ox = int(tx0 + amp * math.sin(oy * freq + phase)
                     + 0.45 * amp * math.sin(oy * freq * 2.7 + phase * 2.0))
            orb_r = 7 if k % 2 else 9
            add_disc(buf, ox, oy, orb_r + 6, col, 0.55)
            add_disc(buf, ox, oy, orb_r, (255, 255, 255), 1.0)

    # --- drifting glowing plankton dots around the bell ---
    state = 13579
    for _ in range(90):
        state = _lcg(state)
        x = 120 + (state % 784)
        state = _lcg(state)
        y = 120 + (state % 760)
        state = _lcg(state)
        b = 40 + (state % 80)
        if (x - JCX) ** 2 / (JRX * JRX) + (y - JCY) ** 2 / (JRY * JRY) < 1.1:
            continue  # keep the bell face clean
        add_px(buf, x, y, b * 0.5, b, b)
        add_px(buf, x + 1, y, b * 0.2, b * 0.4, b * 0.4)


# ---------------------------------------------------------------- PNG writer

def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path, buf):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: None
        raw += buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)  # fixed level -> deterministic
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", comp)
           + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    buf = bytearray(W * H * 3)
    paint_sky(buf)
    paint_stars(buf)
    paint_city(buf)
    paint_city_glow(buf)
    paint_jellyfish(buf)
    path = os.path.join(out_dir, "entry.png")
    write_png(path, buf)
    print("wrote", path)


if __name__ == "__main__":
    main()
