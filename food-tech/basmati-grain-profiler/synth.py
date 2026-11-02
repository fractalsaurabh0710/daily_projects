"""Synthetic rice-on-a-mat photographs with known ground truth.

Real calibration photos are scarce, so every later stage of the profiler is
tested against images whose true kernel length, breadth and chalk fraction are
known exactly. Kernels are superellipses (pointed ends, plump middle), tilted at
random, with an optional opaque chalky patch on the belly, plus sensor noise.
"""
import json
import math
import random

from pngio import write_png

BG, GRAIN, CHALK = 24, 196, 247


def kernel_mask(L, B, angle, pxmm, chalk_frac):
    """Return {(dx,dy): value} for one kernel centred on the origin, sizes in mm."""
    c, s = math.cos(angle), math.sin(angle)
    half = int(L * pxmm / 2) + 3
    pix = {}
    for dy in range(-half, half + 1):
        for dx in range(-half, half + 1):
            u = (dx * c + dy * s) / pxmm      # along the kernel's long axis
            v = (-dx * s + dy * c) / pxmm     # across it
            if (abs(u) / (L / 2)) ** 2.3 + (abs(v) / (B / 2)) ** 2 <= 1.0:
                # Chalk lives in a belly patch, off-centre along the long axis.
                inside = False
                if chalk_frac > 0:
                    k = chalk_frac ** 0.5 * 1.6
                    inside = ((u - 0.12 * L) / (0.34 * L * k)) ** 2 + (v / (0.5 * B * k)) ** 2 <= 1.0
                pix[(dx, dy)] = CHALK if inside else GRAIN
    return pix


def make_sample(path, n=24, pxmm=20, cols=6, seed=1, mix=(("basmati", 1.0),)):
    """Write a PNG and return ground truth. `mix` is ((variety, share), ...)."""
    rng = random.Random(seed)
    # Reference dimensions in mm (cooked-grain elongation is not modelled).
    varieties = {"basmati": (8.3, 1.9), "long-grain": (6.6, 2.1)}
    cell = 11.0                                # mm per grid cell, no overlaps
    rows_n = math.ceil(n / cols)
    W, H = int(cols * cell * pxmm), int(rows_n * cell * pxmm)
    canvas = [bytearray([BG]) * W for _ in range(H)]
    truth = {"pxmm": pxmm, "kernels": []}
    names = [v for v, _ in mix]
    weights = [w for _, w in mix]
    for i in range(n):
        var = rng.choices(names, weights)[0]
        L0, B0 = varieties[var]
        L, B = L0 * rng.uniform(0.93, 1.07), B0 * rng.uniform(0.93, 1.07)
        chalk = rng.choice([0, 0, 0, rng.uniform(0.15, 0.55)])
        ang = rng.uniform(0, math.pi)
        cx = int(((i % cols) + 0.5) * cell * pxmm + rng.uniform(-0.6, 0.6) * pxmm)
        cy = int(((i // cols) + 0.5) * cell * pxmm + rng.uniform(-0.6, 0.6) * pxmm)
        pix = kernel_mask(L, B, ang, pxmm, chalk)
        for (dx, dy), val in pix.items():
            canvas[cy + dy][cx + dx] = val
        area = len(pix)
        truth["kernels"].append({
            "variety": var, "length_mm": round(L, 3), "breadth_mm": round(B, 3),
            "angle": round(ang, 4), "center_px": [cx, cy], "area_px": area,
            "chalk_fraction": round(sum(v == CHALK for v in pix.values()) / area, 4)})
    for row in canvas:                          # sensor noise
        for x in range(W):
            row[x] = max(0, min(255, row[x] + int(rng.gauss(0, 4))))
    write_png(path, W, H, 1, canvas)
    with open(path.rsplit(".", 1)[0] + ".truth.json", "w") as f:
        json.dump(truth, f, indent=1)
    return truth


if __name__ == "__main__":
    import os, tempfile
    from pngio import read_png
    tmp = os.path.join(tempfile.mkdtemp(), "s.png")
    t = make_sample(tmp, n=12, cols=4, seed=3)
    w, h, ch, rows = read_png(tmp)
    assert (w, h, ch) == (4 * 220, 3 * 220, 1)
    assert len(t["kernels"]) == 12
    for k in t["kernels"]:
        # Aspect ratio is basmati-like (>3.5) and the kernel sits inside the frame.
        assert k["length_mm"] / k["breadth_mm"] > 3.5, k
        x, y = k["center_px"]
        assert 0 < x < w and 0 < y < h and k["area_px"] > 1500, k
        assert 0 <= k["chalk_fraction"] < 0.7
    # Pixel statistics: grain pixels outnumber chalk, background dominates.
    flat = b"".join(bytes(r) for r in rows)
    grain = sum(1 for p in flat if p > 120)
    assert abs(grain - sum(k["area_px"] for k in t["kernels"])) < 0.02 * grain
    mixed = make_sample(tmp, n=40, cols=8, seed=5, mix=(("basmati", 0.7), ("long-grain", 0.3)))
    assert 5 < sum(k["variety"] == "long-grain" for k in mixed["kernels"]) < 25
    print("synth: all tests passed")
