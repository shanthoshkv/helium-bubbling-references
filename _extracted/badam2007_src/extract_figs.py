"""Render Badam figure crops and dump Fig. 1 vector strokes."""
from pathlib import Path
import fitz

PDF = Path(__file__).resolve().parents[2] / "C_correlations" / "Badam2007_regimes_bubble_formation_submerged_orifices.pdf"
OUT = Path(__file__).resolve().parent
doc = fitz.open(PDF)

# Page 3 (index 2): Fig 1 bottom-left, Fig 2 right.
p2 = doc[2]
pix = p2.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False)
pix.save(OUT / "page3.png")
print("page3", pix.width, pix.height)

# Page 6 (index 5): Fig 5 left column.
p5 = doc[5]
pix = p5.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False)
pix.save(OUT / "page6.png")
print("page6", pix.width, pix.height)

print("\npage 3 drawings with many items:")
for d in p2.get_drawings():
    n = len(d.get("items") or [])
    if n < 20:
        continue
    r = d["rect"]
    color = d.get("color")
    dashes = d.get("dashes")
    print(
        f"  n={n:4d} color={None if not color else tuple(round(x,3) for x in color)} "
        f"dash={dashes} rect=({r.x0:.1f},{r.y0:.1f},{r.x1:.1f},{r.y1:.1f}) "
        f"w={r.width:.1f} h={r.height:.1f}"
    )
