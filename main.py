#!/usr/bin/env python3
"""IGNITION — a struck match whose flame blooms into a spiral nebula.

Procedural entry for make.fun's ai-excited-01 ("Make the AI judge excited").
Pure Python standard library: the whole image is painted into a float RGB
buffer (deep-space gradient, stars, a bold match silhouette, a layered flame,
a three-arm logarithmic spiral nebula continuous with the flame, drifting
embers, a gentle vignette) and encoded as a PNG with zlib/struct.

Deterministic: every random draw comes from one seeded generator and the
program is run twice by the grader — both runs write identical bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   ->   out/entry.png
"""

import math
import os
import random
import struct
import zlib

# --------------------------------------------------------------------------
# Canvas and palette
# --------------------------------------------------------------------------

W = 1024
H = 1024
S = W / 1024.0  # scale factor: every coordinate below is authored at 1024px

SEED = 20261116

TOP = (5.0, 2.0, 15.0)        # #05020f near-black indigo
BOTTOM = (28.0, 11.0, 54.0)   # #1c0b36 deep violet

STICK_EDGE = (43.0, 21.0, 7.0)
STICK_CORE = (23.0, 11.0, 2.0)    # #170b02
HEAD_BASE = (82.0, 22.0, 9.0)     # dark crimson-brown
HEAD_CHAR = (9.0, 4.0, 2.0)       # charred black

FLAME_OUTER = (255.0, 122.0, 26.0)    # #ff7a1a
FLAME_TIP = (255.0, 143.0, 36.0)
FLAME_MID = (255.0, 181.0, 46.0)      # #ffb52e
FLAME_INNER = (255.0, 243.0, 214.0)   # #fff3d6
FLAME_BASE = (255.0, 217.0, 138.0)


def ramp(t):
    """Nebula colour ramp by normalised radius: white-gold core -> violet rim."""
    stops = (
        (0.00, (255.0, 242.0, 217.0)),
        (0.25, (255.0, 184.0, 89.0)),
        (0.50, (250.0, 115.0, 115.0)),
        (0.75, (217.0, 89.0, 191.0)),
        (1.00, (140.0, 102.0, 242.0)),
    )
    t = min(1.0, max(0.0, t))
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            return (c0[0] + (c1[0] - c0[0]) * f,
                    c0[1] + (c1[1] - c0[1]) * f,
                    c0[2] + (c1[2] - c0[2]) * f)
    return stops[-1][1]


# --------------------------------------------------------------------------
# Buffer helpers
# --------------------------------------------------------------------------

def add_glow(buf, cx, cy, rx, ry, ang, rgb, intensity, power=2.0):
    """Additively blend one soft elliptical glow into the float buffer."""
    ca, sa = math.cos(ang), math.sin(ang)
    reach = max(rx, ry) + 1.0
    x0 = max(0, int(cx - reach))
    x1 = min(W - 1, int(cx + reach))
    y0 = max(0, int(cy - reach))
    y1 = min(H - 1, int(cy + reach))
    ir, ig, ib = rgb[0] * intensity, rgb[1] * intensity, rgb[2] * intensity
    for py in range(y0, y1 + 1):
        dy = py - cy
        base = py * W
        for px in range(x0, x1 + 1):
            dx = px - cx
            du = dx * ca + dy * sa
            dv = -dx * sa + dy * ca
            q2 = (du / rx) * (du / rx) + (dv / ry) * (dv / ry)
            if q2 < 1.0:
                f = (1.0 - math.sqrt(q2)) ** power
                i = (base + px) * 3
                buf[i] += ir * f
                buf[i + 1] += ig * f
                buf[i + 2] += ib * f


def add_dot(buf, cx, cy, radius, rgb, intensity):
    add_glow(buf, cx, cy, radius, radius, 0.0, rgb, intensity, power=2.0)


# --------------------------------------------------------------------------
# Background: vertical gradient + large-scale value noise + stars
# --------------------------------------------------------------------------

def paint_background(buf, rng):
    grid_n = 9
    grid = [rng.uniform(-1.0, 1.0) for _ in range(grid_n * grid_n)]
    amp = 4.5
    row_col = []
    for y in range(H):
        t = (y / (H - 1.0)) ** 1.15
        row_col.append((TOP[0] + (BOTTOM[0] - TOP[0]) * t,
                        TOP[1] + (BOTTOM[1] - TOP[1]) * t,
                        TOP[2] + (BOTTOM[2] - TOP[2]) * t))
    for y in range(H):
        gy = y / (H - 1.0) * (grid_n - 1)
        gyi = min(grid_n - 2, int(gy))
        fy = gy - gyi
        cr, cg, cb = row_col[y]
        base = y * W
        for x in range(W):
            gx = x / (W - 1.0) * (grid_n - 1)
            gxi = min(grid_n - 2, int(gx))
            fx = gx - gxi
            n00 = grid[gyi * grid_n + gxi]
            n10 = grid[gyi * grid_n + gxi + 1]
            n01 = grid[(gyi + 1) * grid_n + gxi]
            n11 = grid[(gyi + 1) * grid_n + gxi + 1]
            n = (n00 * (1 - fx) + n10 * fx) * (1 - fy) + \
                (n01 * (1 - fx) + n11 * fx) * fy
            i = (base + x) * 3
            buf[i] = cr + n * amp
            buf[i + 1] = cg + n * amp
            buf[i + 2] = cb + n * amp * 1.2


def paint_stars(buf, rng):
    tints = ((255.0, 255.0, 255.0), (255.0, 240.0, 214.0), (214.0, 228.0, 255.0))
    for _ in range(500):
        x = rng.uniform(0, W - 1)
        y = rng.uniform(0, H - 1)
        a = rng.uniform(0.10, 0.62)
        c = tints[rng.randrange(len(tints))]
        add_dot(buf, x, y, rng.uniform(0.7, 1.3), c, a)
    for _ in range(14):  # a handful of brighter stars with a soft halo
        x = rng.uniform(20, W - 20)
        y = rng.uniform(20, H - 20)
        c = tints[rng.randrange(len(tints))]
        add_glow(buf, x, y, 5.5, 5.5, 0.0, c, 0.16)
        add_dot(buf, x, y, 1.7, c, 0.85)


# --------------------------------------------------------------------------
# The nebula: a 3-arm logarithmic spiral, tilted and slightly squashed
# --------------------------------------------------------------------------

NEB_C = (600.0 * S, 330.0 * S)
NEB_R = 340.0 * S
NEB_TILT = -0.32          # radians
NEB_SQUASH = 0.82
SPIRAL_RMIN = 12.0
SPIRAL_THETA_MAX = 3.6
SPIRAL_B = math.log(NEB_R / SPIRAL_RMIN) / SPIRAL_THETA_MAX


def spiral_point(arm, theta, radial_jitter=0.0):
    """A point on arm `arm` at spiral parameter theta, in canvas pixels."""
    r = (SPIRAL_RMIN * math.exp(SPIRAL_B * theta) + radial_jitter) * S
    a = arm * (2.0 * math.pi / 3.0) + theta
    x, y = r * math.cos(a), r * math.sin(a) * NEB_SQUASH
    ca, sa = math.cos(NEB_TILT), math.sin(NEB_TILT)
    return (NEB_C[0] + x * ca - y * sa, NEB_C[1] + x * sa + y * ca)


def paint_nebula(buf, rng):
    # Large, very soft glows underneath everything.
    add_glow(buf, NEB_C[0], NEB_C[1], 230 * S, 190 * S, NEB_TILT,
             (255.0, 158.0, 64.0), 0.34)
    mx, my = spiral_point(1, 3.0)
    add_glow(buf, mx, my, 185 * S, 155 * S, NEB_TILT, (232.0, 84.0, 178.0), 0.21)
    tx, ty = spiral_point(2, 2.7)
    add_glow(buf, tx, ty, 200 * S, 165 * S, NEB_TILT, (96.0, 84.0, 216.0), 0.20)

    # A continuous ribbon of soft "gas" glows along each arm, so the arms
    # have luminous body and the dots sit in them like stars in gas.
    for arm in range(3):
        for k in range(30):
            theta = SPIRAL_THETA_MAX * (k / 29.0) ** 1.15
            r = SPIRAL_RMIN * math.exp(SPIRAL_B * theta)
            t = r / NEB_R
            gx, gy = spiral_point(arm, theta)
            gr = (9.0 + 0.17 * r) * S
            add_glow(buf, gx, gy, gr, gr * 0.85, NEB_TILT,
                     ramp(t), 0.10 * (1.0 - t * 0.35))

    # The arms: thousands of tiny additive dots, dense and bright at the core.
    n_dots = 9000
    for i in range(n_dots):
        arm = i % 3
        s = rng.random()
        theta = SPIRAL_THETA_MAX * (s ** 1.5)
        r = SPIRAL_RMIN * math.exp(SPIRAL_B * theta)
        t = r / NEB_R
        # Perpendicular jitter widens the arm with radius.
        width = 6.0 + 0.115 * r
        off = rng.gauss(0.0, width * 0.62)
        px, py = spiral_point(arm, theta)
        # Offset perpendicular to the arm's local direction.
        qx, qy = spiral_point(arm, theta + 0.02)
        dx, dy = qx - px, qy - py
        dl = math.hypot(dx, dy) or 1.0
        px += -dy / dl * off * S
        py += dx / dl * off * S
        bright = (1.0 - t) ** 0.38 * rng.uniform(0.55, 1.05)
        if rng.random() < 0.03:
            bright *= 1.8  # a few sparkle dots
        radius = 1.3 + (1.0 - t) * 2.1 + rng.random() * 1.1
        add_dot(buf, px, py, radius * S, ramp(t), bright)

    # A dense, bright core cluster.
    for _ in range(500):
        ang = rng.uniform(0, 2.0 * math.pi)
        rr = (rng.random() ** 2.2) * 42.0 * S
        px = NEB_C[0] + math.cos(ang) * rr
        py = NEB_C[1] + math.sin(ang) * rr * NEB_SQUASH
        add_dot(buf, px, py, rng.uniform(1.0, 2.6) * S,
                ramp(rr / (NEB_R * 2.2)), rng.uniform(0.5, 1.05))
    add_glow(buf, NEB_C[0], NEB_C[1], 95 * S, 80 * S, NEB_TILT,
             (255.0, 214.0, 140.0), 0.42)


# --------------------------------------------------------------------------
# The match: bold dark diagonal silhouette + head, entering bottom-left
# --------------------------------------------------------------------------

TAIL = (119.0 * S, 1017.0 * S)
HEAD = (555.0 * S, 395.0 * S)
AX = HEAD[0] - TAIL[0]
AY = HEAD[1] - TAIL[1]
ALEN = math.hypot(AX, AY)
DIR = (AX / ALEN, AY / ALEN)            # up the stick, toward the flame
PERP = (-DIR[1], DIR[0])


def paint_match(buf, rng):
    x0 = max(0, int(min(TAIL[0], HEAD[0]) - 30 * S))
    x1 = min(W - 1, int(max(TAIL[0], HEAD[0]) + 30 * S))
    y0 = max(0, int(min(TAIL[1], HEAD[1]) - 30 * S))
    y1 = min(H - 1, int(max(TAIL[1], HEAD[1]) + 30 * S))
    streaks = (-0.38, 0.05, 0.42)
    for py in range(y0, y1 + 1):
        ry = py - TAIL[1]
        base = py * W
        for px in range(x0, x1 + 1):
            rx = px - TAIL[0]
            u = (rx * DIR[0] + ry * DIR[1]) / ALEN
            if u < -0.01 or u > 1.01:
                continue
            v = rx * PERP[0] + ry * PERP[1]
            halfw = (15.5 + (9.0 - 15.5) * min(1.0, max(0.0, u))) * S
            av = abs(v)
            if av > halfw + 1.0:
                continue
            frac = av / halfw
            # Core in the middle, slightly lighter warm edge.
            cr = STICK_CORE[0] + (STICK_EDGE[0] - STICK_CORE[0]) * frac
            cg = STICK_CORE[1] + (STICK_EDGE[1] - STICK_CORE[1]) * frac
            cb = STICK_CORE[2] + (STICK_EDGE[2] - STICK_CORE[2]) * frac
            # Faint grain streaks running along the wood.
            vf = v / halfw
            for si, sc in enumerate(streaks):
                d = (vf - sc) / 0.07
                g = math.exp(-d * d) * (0.5 + 0.5 * math.sin(u * 44.0 + si * 2.1))
                cr += 11.0 * g
                cg += 5.0 * g
            # A whisper of warm rim light on the upper edge.
            if v < 0:
                rim = (1.0 - frac) * 0.35 + 0.65
                cr += 9.0 * rim * frac
                cg += 3.5 * rim * frac
            alpha = min(1.0, max(0.0, halfw + 0.5 - av))
            i = (base + px) * 3
            buf[i] = buf[i] * (1 - alpha) + cr * alpha
            buf[i + 1] = buf[i + 1] * (1 - alpha) + cg * alpha
            buf[i + 2] = buf[i + 2] * (1 - alpha) + cb * alpha


def paint_head(buf, rng):
    cx = HEAD[0] + DIR[0] * 6 * S
    cy = HEAD[1] + DIR[1] * 6 * S
    ra, rb = 24.0 * S, 16.0 * S
    reach = 29 * S
    x0 = max(0, int(cx - reach))
    x1 = min(W - 1, int(cx + reach))
    y0 = max(0, int(cy - reach))
    y1 = min(H - 1, int(cy + reach))
    for py in range(y0, y1 + 1):
        ry = py - cy
        base = py * W
        for px in range(x0, x1 + 1):
            rx = px - cx
            du = rx * DIR[0] + ry * DIR[1]
            dv = rx * PERP[0] + ry * PERP[1]
            q = math.sqrt((du / ra) ** 2 + (dv / rb) ** 2)
            if q > 1.05:
                continue
            # Charred toward the flame side (positive du).
            charf = min(1.0, max(0.0, du / ra * 0.5 + 0.5)) ** 1.4
            cr = HEAD_BASE[0] + (HEAD_CHAR[0] - HEAD_BASE[0]) * charf
            cg = HEAD_BASE[1] + (HEAD_CHAR[1] - HEAD_BASE[1]) * charf
            cb = HEAD_BASE[2] + (HEAD_CHAR[2] - HEAD_BASE[2]) * charf
            # A hot ember blush where the flame takes hold.
            if du > 4 * S and q < 0.62:
                hot = (1.0 - q) * 0.8
                cr += 120.0 * hot
                cg += 30.0 * hot
            alpha = min(1.0, max(0.0, (1.05 - q) * 4.0))
            i = (base + px) * 3
            buf[i] = buf[i] * (1 - alpha) + cr * alpha
            buf[i + 1] = buf[i + 1] * (1 - alpha) + cg * alpha
            buf[i + 2] = buf[i + 2] * (1 - alpha) + cb * alpha


# --------------------------------------------------------------------------
# The flame: layered soft ellipses along the stick's direction
# --------------------------------------------------------------------------

def paint_flame(buf, rng):
    hx, hy = HEAD
    dx, dy = DIR
    px_, py_ = PERP

    def layer(dist, off, along, across, rgb, inten):
        cx = hx + dx * dist * S + px_ * off * S
        cy = hy + dy * dist * S + py_ * off * S
        ang = math.atan2(dy, dx)
        add_glow(buf, cx, cy, along * S, across * S, ang, rgb, inten)

    # A broad halo first, so the flame blooms into the nebula around it.
    add_glow(buf, hx + dx * 40 * S, hy + dy * 40 * S, 190 * S, 190 * S, 0.0,
             (255.0, 140.0, 46.0), 0.17)
    layer(58, 4, 108, 48, FLAME_OUTER, 0.82)    # outer orange body
    layer(112, 10, 52, 20, FLAME_TIP, 0.55)     # licking tip
    layer(44, 1, 70, 30, FLAME_MID, 0.98)       # gold
    layer(28, 0, 42, 17, FLAME_INNER, 1.08)     # near-white core
    layer(10, 0, 19, 12, FLAME_BASE, 0.92)      # bright base at the head


# --------------------------------------------------------------------------
# Embers drifting up-right from the flame
# --------------------------------------------------------------------------

def paint_embers(buf, rng):
    ox = HEAD[0] + DIR[0] * 55 * S
    oy = HEAD[1] + DIR[1] * 55 * S
    drift = (0.75, -0.66)
    cols = (FLAME_INNER, FLAME_MID, FLAME_OUTER)
    weights = (0.3, 0.4, 0.3)
    for _ in range(220):
        t = rng.random() ** 1.3
        dist = t * 400.0 * S
        spread = (8.0 + t * 64.0) * S
        off = rng.gauss(0.0, spread)
        x = ox + drift[0] * dist + (-drift[1]) * off
        y = oy + drift[1] * dist + drift[0] * off
        r = rng.random()
        c = cols[0] if r < weights[0] else (cols[1] if r < weights[0] + weights[1] else cols[2])
        bright = (1.0 - t * 0.85) * rng.uniform(0.45, 1.0)
        add_dot(buf, x, y, rng.uniform(0.8, 2.6) * S, c, bright)


# --------------------------------------------------------------------------
# Finish: vignette, a whisper of grain, clamp, encode
# --------------------------------------------------------------------------

def finish(buf, rng):
    out = bytearray(W * H * 3)
    cx, cy = W / 2.0, H / 2.0
    norm = (0.5 * W) ** 2
    for y in range(H):
        dy2 = (y - cy) ** 2
        base = y * W
        for x in range(W):
            q = ((x - cx) ** 2 + dy2) / norm
            s = min(1.0, max(0.0, (q - 0.6) / 1.4))
            f = 1.0 - 0.25 * s
            grain = rng.uniform(-1.4, 1.4)
            i = (base + x) * 3
            for c in range(3):
                v = buf[i + c] * f + grain
                out[i + c] = 0 if v < 0.0 else (255 if v > 255.0 else int(v + 0.5))
    return out


def encode_png(pixels):
    """Encode the RGB byte buffer as a PNG, trying a few row filters and
    keeping whichever compresses smallest (all standard PNG filters)."""
    stride = W * 3
    raw0 = bytearray()
    raw1 = bytearray()
    raw2 = bytearray()
    prev = bytearray(stride)
    for y in range(H):
        row = pixels[y * stride:(y + 1) * stride]
        raw0.append(0)
        raw0 += row
        raw1.append(1)
        for i in range(stride):
            left = row[i - 3] if i >= 3 else 0
            raw1.append((row[i] - left) & 0xFF)
        raw2.append(2)
        for i in range(stride):
            raw2.append((row[i] - prev[i]) & 0xFF)
        prev = row
    best = None
    for raw in (raw0, raw1, raw2):
        comp = zlib.compress(bytes(raw), 9)
        if best is None or len(comp) < len(best):
            best = comp

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", best) + chunk(b"IEND", b""))


def main():
    rng = random.Random(SEED)
    buf = [0.0] * (W * H * 3)
    paint_background(buf, rng)
    paint_stars(buf, rng)
    paint_nebula(buf, rng)
    paint_match(buf, rng)
    paint_head(buf, rng)
    paint_flame(buf, rng)
    paint_embers(buf, rng)
    pixels = finish(buf, rng)
    png = encode_png(pixels)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s (%dx%d, %d bytes)" % (path, W, H, len(png)))


if __name__ == "__main__":
    main()
