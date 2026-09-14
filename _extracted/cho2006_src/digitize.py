"""Digitize Cho2006 Figs. 5, 8, 10, 12 from native vector paths and filled markers.

Fig. 10 helium-temperature assignment follows the paper's own arrows, not the prose
that swapped 114 K / 288 K against the legend:
  black squares  r=1.34  -> 114 K  (most cooling)
  red circles    r=0.50  -> 140 K
  blue triangles r=1.05  -> 288 K  (least cooling)
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np

PDF = Path(__file__).resolve().parents[2] / "Cho2006_helium_injection_cooling_LOX_pressurized.pdf"
OUT = Path(__file__).resolve().parents[1]
SUITE_OUT = Path(__file__).resolve().parents[3] / "helium_bubbler_suite" / "references" / "_extracted"


def _key(c):
    return tuple(round(x, 3) for x in c) if c else None


def _pick(matches, ref, idx):
    if len(matches) == 1 or ref is None:
        return matches[0]
    return min(matches, key=lambda m: abs(m[idx] - ref))


def calib(page, x_ticks, y_ticks, region):
    x0, y0, x1, y1 = region
    found = {}
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            for s in line.get("spans", []):
                t = s["text"].strip()
                if t not in x_ticks and t not in y_ticks:
                    continue
                bx0, by0, bx1, by1 = s["bbox"]
                cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
                if not (x0 <= cx <= x1 and y0 <= cy <= y1):
                    continue
                found.setdefault(t, []).append((cx, cy))
    unambiguous_x_rows = [v[0][1] for k, v in found.items() if k in x_ticks and len(v) == 1]
    unambiguous_y_cols = [v[0][0] for k, v in found.items() if k in y_ticks and len(v) == 1]
    x_row = float(np.median(unambiguous_x_rows)) if unambiguous_x_rows else None
    y_col = float(np.median(unambiguous_y_cols)) if unambiguous_y_cols else None
    xs = [(_pick(found[k], x_row, 1)[0], v) for k, v in x_ticks.items() if k in found]
    ys = [(_pick(found[k], y_col, 0)[1], v) for k, v in y_ticks.items() if k in found]
    xs.sort()
    ys.sort()
    if len(xs) < 2 or len(ys) < 2:
        raise RuntimeError(f"calibration failed: x={xs}, y={ys}")
    px = np.polyfit([p for p, _ in xs], [v for _, v in xs], 1)
    py = np.polyfit([p for p, _ in ys], [v for _, v in ys], 1)
    return px, py


def _in_box(x, y, box):
    x0, y0, x1, y1 = box
    return x0 <= x <= x1 and y0 <= y <= y1


def markers(page, fill, plot_bbox, legend_box=None):
    """Filled marker centres. Legend swatches sit in ``legend_box`` (PDF coords)."""
    x0, y0, x1, y1 = plot_bbox
    raw = []
    for d in page.get_drawings():
        if _key(d.get("fill")) != fill:
            continue
        r = d["rect"]
        cx, cy = (r.x0 + r.x1) / 2.0, (r.y0 + r.y1) / 2.0
        if not (x0 <= cx <= x1 and y0 <= cy <= y1):
            continue
        if legend_box and _in_box(cx, cy, legend_box):
            continue
        if r.width > 8.0 or r.height > 8.0 or r.width < 0.5 or r.height < 0.5:
            continue
        raw.append((cx, cy, len(d.get("items", []))))
    if not raw:
        return []
    n_counts: dict[int, int] = defaultdict(int)
    for _, _, n in raw:
        n_counts[n] += 1
    n_keep, _ = max(n_counts.items(), key=lambda kv: kv[1])
    pts = [(cx, cy) for cx, cy, n in raw if n == n_keep]
    pts.sort(key=lambda p: p[0])
    kept = []
    for p in pts:
        if kept and abs(p[0] - kept[-1][0]) < 0.35:
            continue
        kept.append(p)
    return kept


def polyline(page, color, plot_bbox, legend_box=None, min_items=40):
    """Long curve strokes. Skips the axes frame, legend, and short arrow decorations."""
    x0, y0, x1, y1 = plot_bbox
    pts = []
    for d in page.get_drawings():
        if _key(d.get("color")) != color:
            continue
        if len(d["items"]) < min_items:
            continue
        r = d["rect"]
        if r.width > 0.92 * (x1 - x0) and r.height > 0.92 * (y1 - y0):
            continue
        # annotation ellipses are squat; real T(t) traces span most of the time axis
        if r.width < 0.55 * (x1 - x0):
            continue
        for item in d["items"]:
            if item[0] != "l":
                continue
            for p in (item[1], item[2]):
                if x0 <= p.x <= x1 and y0 <= p.y <= y1:
                    if legend_box and _in_box(p.x, p.y, legend_box):
                        continue
                    pts.append((p.x, p.y))
    if not pts:
        return np.array([]), np.array([])
    arr = np.array(pts)
    order = np.argsort(arr[:, 0])
    arr = arr[order]
    _, idx = np.unique(np.round(arr[:, 0], 2), return_index=True)
    arr = arr[np.sort(idx)]
    return arr[:, 0], arr[:, 1]


def to_data(x_px, y_px, px, py):
    return np.polyval(px, np.asarray(x_px, dtype=float)), np.polyval(py, np.asarray(y_px, dtype=float))


def resample(t, T, t_grid):
    """1 Hz linear interpolation of the extracted vertices. No cubic overshoot.

    Holds the first/last sample only outside the extracted window -- never invents a slope
    before the first marker or after the last.
    """
    t = np.asarray(t, dtype=float)
    T = np.asarray(T, dtype=float)
    if t.size == 0:
        return np.full(t_grid.shape, np.nan)
    order = np.argsort(t)
    t, T = t[order], T[order]
    _, idx = np.unique(np.round(t, 4), return_index=True)
    t, T = t[idx], T[idx]
    if t.size == 1:
        return np.full(t_grid.shape, T[0])
    return np.interp(t_grid, t, T, left=T[0], right=T[-1])


def series_from_markers(page, fill, plot, legend, px, py, t_grid):
    m = markers(page, fill, plot, legend)
    t, T = to_data([p[0] for p in m], [p[1] for p in m], px, py)
    print(f"    markers n={len(m)} t={t[0]:.0f}->{t[-1]:.0f} T={T[0]:.2f}->{T[-1]:.2f}")
    return resample(t, T, t_grid)


def series_from_polyline(page, color, plot, legend, px, py, t_grid, fill=None):
    x, y = polyline(page, color, plot, legend)
    if len(x) < 5 and fill is not None:
        print("    polyline empty, falling back to markers")
        return series_from_markers(page, fill, plot, legend, px, py, t_grid)
    t, T = to_data(x, y, px, py)
    print(f"    polyline n={len(t)} t={t[0]:.0f}->{t[-1]:.0f} T={T[0]:.2f}->{T[-1]:.2f}")
    return resample(t, T, t_grid)


def write_csv(path: Path, t_grid, series: dict[str, np.ndarray], header_comment: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(header_comment)
        w = csv.writer(f)
        w.writerow(["time_s"] + list(series.keys()))
        for i, t in enumerate(t_grid):
            w.writerow([int(t)] + [f"{series[k][i]:.4f}" for k in series])


def copy_to_suite(path: Path) -> None:
    if SUITE_OUT.exists():
        (SUITE_OUT / path.name).write_bytes(path.read_bytes())


BLACK = (0.0, 0.0, 0.0)
RED = (1.0, 0.0, 0.0)
GREEN = (0.0, 1.0, 0.0)
BLUE = (0.0, 0.0, 1.0)
CYAN = (0.0, 1.0, 1.0)
MAGENTA = (1.0, 0.0, 1.0)
DARK = (0.137, 0.122, 0.125)
ORANGE = (0.924, 0.173, 0.18)
TEAL = (0.0, 0.666, 0.309)
NAVY = (0.199, 0.232, 0.593)


def main() -> int:
    if not PDF.exists():
        raise SystemExit(f"PDF not found: {PDF}")
    doc = fitz.open(PDF)

    # ----- Fig. 5 (page 8): pressure sweep -----
    print("Fig. 5")
    p8 = doc[7]
    fig5_plot = (80.0, 70.0, 280.0, 224.0)
    # Actual legend frame is (181.7, 131.5, 271.1, 167.9). A taller box ate the P=3 bar
    # traces that run just above it (T ~ 92.5-93.3 K, t ~ 750-1000 s).
    fig5_legend = (181.0, 130.0, 272.0, 169.0)
    px5, py5 = calib(
        p8,
        {str(v): float(v) for v in (0, 200, 400, 600, 800, 1000, 1200, 1400)},
        {str(v): float(v) for v in range(86, 96)},
        (50.0, 60.0, 290.0, 245.0),
    )
    t5 = np.arange(0, 1401, 1)
    fig5 = {
        "P1bar_measured": series_from_markers(p8, DARK, fig5_plot, fig5_legend, px5, py5, t5),
        "P3bar_measured": series_from_markers(p8, ORANGE, fig5_plot, fig5_legend, px5, py5, t5),
        "P1bar_calculated": series_from_polyline(p8, TEAL, fig5_plot, fig5_legend, px5, py5, t5),
        "P3bar_calculated": series_from_polyline(p8, NAVY, fig5_plot, fig5_legend, px5, py5, t5),
    }
    write_csv(
        OUT / "Cho2006_fig5_pressure_sweep.csv", t5, fig5,
        "# Cho et al. Cryogenics 46 (2006) 778-793, Fig. 5\n"
        "# LOX T vs time, T_LOX,i=91 K, T_He=288 K.\n"
        "# P=1 bar measured/calculated (V_He/V_LOX=1.39 min^-1, 100 L/min);\n"
        "# P=3 bar measured/calculated (V_He/V_LOX=1.21 min^-1, 87 L/min).\n"
        "# Digitized from vector markers (measured) and polylines (calculated); legend frame excluded.\n"
        "# 1 Hz linear interpolation of extracted vertices (no cubic overshoot).\n",
    )

    # ----- Fig. 8 (page 9): flow-rate sweep -----
    print("Fig. 8")
    p9 = doc[8]
    fig8_plot = (66.0, 540.0, 278.0, 705.0)
    # No drawn legend frame; cover the six swatch+label rows on the right (y=567-620).
    fig8_legend = (180.0, 548.0, 278.0, 625.0)
    px8, py8 = calib(
        p9,
        {str(v): float(v) for v in (0, 200, 400, 600, 800, 1000, 1200, 1400)},
        {str(v): float(v) for v in range(89, 104)},
        (40.0, 530.0, 290.0, 720.0),
    )
    t8 = np.arange(0, 1401, 1)
    fig8 = {
        "r0.81_measured": series_from_markers(p9, BLACK, fig8_plot, fig8_legend, px8, py8, t8),
        "r1.21_measured": series_from_markers(p9, RED, fig8_plot, fig8_legend, px8, py8, t8),
        "r1.34_measured": series_from_markers(p9, GREEN, fig8_plot, fig8_legend, px8, py8, t8),
        "r0.81_calculated": series_from_polyline(p9, BLUE, fig8_plot, fig8_legend, px8, py8, t8),
        "r1.21_calculated": series_from_polyline(p9, CYAN, fig8_plot, fig8_legend, px8, py8, t8),
        "r1.34_calculated": series_from_polyline(p9, MAGENTA, fig8_plot, fig8_legend, px8, py8, t8, fill=MAGENTA),
    }
    write_csv(
        OUT / "Cho2006_fig8_flowrate_sweep.csv", t8, fig8,
        "# Cho et al. Cryogenics 46 (2006) 778-793, Fig. 8\n"
        "# LOX T vs time, P=3 bar, T_He=288 K.\n"
        "# r=0.81 and 1.21 min^-1 at T0=91 K (subcooled, warming);\n"
        "# r=1.34 min^-1 at T0=102 K (saturated, cooling).\n"
        "# 1 Hz linear interpolation of extracted vertices (no cubic overshoot).\n",
    )

    # ----- Fig. 10 (page 9): helium temperature. Assignment from the figure ARROWS. -----
    print("Fig. 10")
    fig10_plot = (334.0, 540.0, 545.0, 705.0)
    # Actual legend frame is (500.9, 562.4, 540.1, 594.6). Keep it tight so t=600 s markers stay.
    fig10_legend = (498.0, 560.0, 542.0, 597.0)
    px10, py10 = calib(
        p9,
        {str(v): float(v) for v in (0, 100, 200, 300, 400, 500, 600)},
        {str(v): float(v) for v in range(83, 92)},
        (310.0, 530.0, 560.0, 720.0),
    )
    t10 = np.arange(0, 601, 1)
    # Arrows on the printed figure: black squares = 114 K, red circles = 140 K, blue triangles = 288 K.
    fig10 = {
        "T114K_r1.34_measured": series_from_markers(p9, BLACK, fig10_plot, fig10_legend, px10, py10, t10),
        "T140K_r0.5_measured": series_from_markers(p9, RED, fig10_plot, fig10_legend, px10, py10, t10),
        "T288K_r1.05_measured": series_from_markers(p9, BLUE, fig10_plot, fig10_legend, px10, py10, t10),
    }
    write_csv(
        OUT / "Cho2006_fig10_helium_temp_sweep.csv", t10, fig10,
        "# Cho et al. Cryogenics 46 (2006) 778-793, Fig. 10\n"
        "# LOX T vs time, P=1 bar. Experiment only.\n"
        "# Series assigned from the figure's own arrows (not the swapped prose):\n"
        "#   black squares  r=1.34 min^-1 -> T_He=114 K (most cooling, ~83.5 K at 600 s)\n"
        "#   red circles    r=0.50 min^-1 -> T_He=140 K (~85.7 K at 600 s)\n"
        "#   blue triangles r=1.05 min^-1 -> T_He=288 K (least cooling, ~87.2 K at 600 s)\n"
        "# Matches Baldwin 2023 Table 2 cases 6/7/8 (dT_exp 4.0 / 4.6 / 6.8 K).\n"
        "# The prose sentence that puts 288 K at r=1.34 is a typesetting swap; the arrows win.\n"
        "# 1 Hz linear interpolation of extracted vertices (no cubic overshoot).\n",
    )

    # ----- Fig. 12 (page 10): pressurized helium temperature -----
    print("Fig. 12")
    p10 = doc[9]
    fig12_plot = (347.0, 70.0, 555.0, 226.0)
    # Actual legend frame is (410.1, 82.8, 545.5, 120.1).
    fig12_legend = (408.0, 81.0, 547.0, 122.0)
    px12, py12 = calib(
        p10,
        {str(v): float(v) for v in (0, 200, 400, 600, 800, 1000, 1200, 1400)},
        {str(v): float(v) for v in (86, 88, 90, 92, 94, 96, 98, 100, 102)},
        (320.0, 60.0, 570.0, 245.0),
    )
    t12 = np.arange(0, 1401, 1)
    fig12 = {
        "T288K_P3bar_measured": series_from_markers(p10, DARK, fig12_plot, fig12_legend, px12, py12, t12),
        "T114K_P3p5bar_measured": series_from_markers(p10, ORANGE, fig12_plot, fig12_legend, px12, py12, t12),
        "T288K_P3bar_calculated": series_from_polyline(p10, TEAL, fig12_plot, fig12_legend, px12, py12, t12),
        "T114K_P3p5bar_calculated": series_from_polyline(p10, NAVY, fig12_plot, fig12_legend, px12, py12, t12),
    }
    write_csv(
        OUT / "Cho2006_fig12_he_temp_pressurized.csv", t12, fig12,
        "# Cho et al. Cryogenics 46 (2006) 778-793, Fig. 12\n"
        "# 288 K He at 3 bar, V_He/V_LOX=1.21 min^-1, T0=91 K (warms);\n"
        "# 114 K He at 3.5 bar, V_He/V_LOX=1.3 min^-1, T0=99 K (cools to 86.8 K at 1500 s).\n"
        "# 1 Hz linear interpolation of extracted vertices (no cubic overshoot).\n",
    )

    for src in (
        OUT / "Cho2006_fig5_pressure_sweep.csv",
        OUT / "Cho2006_fig8_flowrate_sweep.csv",
        OUT / "Cho2006_fig10_helium_temp_sweep.csv",
        OUT / "Cho2006_fig12_he_temp_pressurized.csv",
    ):
        copy_to_suite(src)
        print("wrote", src.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
