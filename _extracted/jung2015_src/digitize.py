"""Digitize Jung2015 Figs. 4-5 from native vector paths in the PDF (not pixel-guessed).
Chart lines are real vector strokes; axis tick labels give exact pixel<->data calibration.
Run once; writes the two 3601-row (0..3600 s) CSVs used by the validation/sweep tabs.
"""
import csv
import sys
from pathlib import Path

import fitz  # pymupdf
import numpy as np

PDF = Path(__file__).parent / "Jung2015.pdf"
OUT = Path(__file__).parents[1]  # references/_extracted


def _pick(matches, ref, idx):
    """A tick label's text (e.g. "0") can also appear elsewhere on the page (a caption's "= 0",
    a stray page number) -- get_text returns every occurrence, and just taking the first one
    silently calibrated against the wrong pixel position. All the real tick labels of one axis
    share the same row (x-axis, idx=1 i.e. y-coordinate) or column (y-axis, idx=0); pick
    whichever match lines up with that, not whichever the text scan happened to see first."""
    if len(matches) == 1 or ref is None:
        return matches[0]
    return min(matches, key=lambda m: abs(m[idx] - ref))


def calib(page, x_ticks, y_ticks):
    """x_ticks/y_ticks: {label_text: data_value}. Returns (x_px->t, y_px->T) linear maps."""
    tp = page.get_text("dict")
    found = {}
    for b in tp["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"].strip()
                if t in x_ticks or t in y_ticks:
                    x0, y0, x1, y1 = s["bbox"]
                    found.setdefault(t, []).append(((x0 + x1) / 2, (y0 + y1) / 2))
    unambiguous_x_rows = [v[0][1] for k, v in found.items() if k in x_ticks and len(v) == 1]
    unambiguous_y_cols = [v[0][0] for k, v in found.items() if k in y_ticks and len(v) == 1]
    x_row = np.median(unambiguous_x_rows) if unambiguous_x_rows else None
    y_col = np.median(unambiguous_y_cols) if unambiguous_y_cols else None
    xs = [(_pick(found[k], x_row, 1)[0], v) for k, v in x_ticks.items() if k in found]
    ys = [(_pick(found[k], y_col, 0)[1], v) for k, v in y_ticks.items() if k in found]
    xs.sort(); ys.sort()
    # linear fit pixel->data
    px = np.polyfit([p for p, _ in xs], [v for _, v in xs], 1)
    py = np.polyfit([p for p, _ in ys], [v for _, v in ys], 1)
    return px, py


def series_points(page, color, px, py):
    def key(c):
        return tuple(round(x, 2) for x in c) if c else None

    target = tuple(round(x, 2) for x in color)
    pts = []
    for d in page.get_drawings():
        if key(d.get("color")) != target:
            continue
        # The legend swatch is drawn in the same colour as its curve but as a single short
        # segment (len(items) == 1); every real curve is 50+ dash/solid segments. Without this
        # filter the swatch's one stray point (sitting inside the plot area, over the legend box)
        # gets treated as a real sample and produces a sharp spike at that time value.
        if len(d["items"]) < 10:
            continue
        for item in d["items"]:
            if item[0] == "l":
                for p in (item[1], item[2]):
                    pts.append((p.x, p.y))
    t = np.polyval(px, [p[0] for p in pts])
    T = np.polyval(py, [p[1] for p in pts])
    order = np.argsort(t)
    t, T = t[order], T[order]
    # dedupe near-identical x from overlapping segments
    t_u, idx = np.unique(np.round(t, 3), return_index=True)
    return t_u, T[idx]


def resample(t, T, t_grid):
    t = np.clip(t, t_grid[0], t_grid[-1])
    return np.interp(t_grid, t, T)


def write_csv(path, t_grid, series):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s"] + list(series.keys()))
        for i, t in enumerate(t_grid):
            w.writerow([int(t)] + [f"{series[k][i]:.4f}" for k in series])


def main():
    doc = fitz.open(PDF)
    t_grid = np.arange(0, 3601, 1)
    x_ticks = {str(v): v for v in (0, 500, 1000, 1500, 2000, 2500, 3000, 3500)}

    # Fig. 4 (page index 4): LOX temperature vs time, tank pressure sweep
    p4 = doc[4]
    y_ticks_4 = {f"{v:g}": v for v in np.arange(85, 90.01, 0.5)}
    px4, py4 = calib(p4, x_ticks, y_ticks_4)
    colors_4 = {
        "Pt_2.0bar": (0.0, 0.0, 1.0),
        "Pt_1.8bar": (0.0, 0.5, 0.0),
        "Pt_1.6bar": (1.0, 0.0, 0.0),
        "Pt_1.4bar": (0.0, 0.75, 0.75),
        "Pt_1.2bar": (0.75, 0.0, 0.75),
    }
    series_4 = {}
    for name, color in colors_4.items():
        t, T = series_points(p4, color, px4, py4)
        series_4[name] = resample(t, T, t_grid)
    write_csv(OUT / "Jung2015_fig4_pressure_sweep.csv", t_grid, series_4)

    # Fig. 5 (page index 5): LOX temperature vs time, helium injection temperature sweep
    p5 = doc[5]
    y_ticks_5 = {f"{v:g}": v for v in np.arange(86, 90.01, 0.5)}
    px5, py5 = calib(p5, x_ticks, y_ticks_5)
    colors_5 = {
        "Tg_288K": (0.0, 0.0, 1.0),
        "Tg_200K": (0.0, 0.5, 0.0),
        "Tg_120K": (1.0, 0.0, 0.0),
        "Tg_90K": (0.0, 0.75, 0.75),
    }
    series_5 = {}
    for name, color in colors_5.items():
        t, T = series_points(p5, color, px5, py5)
        series_5[name] = resample(t, T, t_grid)
    write_csv(OUT / "Jung2015_fig5_helium_temp_sweep.csv", t_grid, series_5)

    for name, series in (("fig4", series_4), ("fig5", series_5)):
        for k, v in series.items():
            print(f"{name} {k}: t=0 -> {v[0]:.2f} K, t=3600 -> {v[-1]:.2f} K")


if __name__ == "__main__":
    sys.exit(main())
