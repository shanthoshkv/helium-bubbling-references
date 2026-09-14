"""List Badam 2007 page drawings so we can digitize Figs. 1 and 5."""
from collections import defaultdict
from pathlib import Path
import fitz

PDF = Path(__file__).resolve().parents[2] / "C_correlations" / "Badam2007_regimes_bubble_formation_submerged_orifices.pdf"
doc = fitz.open(PDF)
print("pages", doc.page_count)
for i, page in enumerate(doc):
    print(f"\n=== page {i+1} {page.rect} ===")
    drawings = page.get_drawings()
    print("drawings", len(drawings))
    fills = defaultdict(int)
    strokes = defaultdict(int)
    for d in drawings:
        fill = d.get("fill")
        color = d.get("color")
        n = len(d.get("items") or [])
        r = d["rect"]
        if fill:
            fills[tuple(round(x, 3) for x in fill)] += 1
        if color:
            strokes[(tuple(round(x, 3) for x in color), n)] += 1
        if n >= 8 and r.width > 20:
            print(
                f"  stroke={None if not color else tuple(round(x,3) for x in color)} "
                f"fill={None if not fill else tuple(round(x,3) for x in fill)} "
                f"n={n} dash={d.get('dashes')} w={r.width:.1f} h={r.height:.1f} "
                f"rect=({r.x0:.1f},{r.y0:.1f},{r.x1:.1f},{r.y1:.1f})"
            )
    if fills:
        print(" fills", dict(fills))
    big = [(k, v) for k, v in strokes.items() if v >= 1 and k[1] >= 5]
    if big:
        print(" stroke clusters", sorted(big, key=lambda kv: -kv[1])[:12])
