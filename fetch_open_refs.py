"""Download the open-access references for the Helium Bubbler & LOX Subcooling Suite.

Run:  py -3.11 references/fetch_open_refs.py

Only open-access sources are fetched. Paywalled sources (ScienceDirect, Springer,
AIAA, Begell) are listed in MANIFEST.md as `paywalled-NOT-obtained` and must be
acquired manually through institutional access; see section 1.4 of the master prompt.

Stdlib only, no dependencies.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# (tier_dir, cite_key, source_spec)
#   source_spec is either ("url", <direct url>) or ("ntrs", <ntrs document id>)
REFS: list[tuple[str, str, tuple[str, str]]] = [
    # --- Tier A: design basis -------------------------------------------------
    ("A_design_basis", "Ramesh2014_subcooling_cryogenic_liquids_helium_bubbling",
     ("url", "https://www.enggjournals.com/ijet/docs/IJET14-06-01-055.pdf")),
    ("A_design_basis", "Stochl1969_gaseous_hydrogen_requirements_LH2_discharge",
     ("ntrs", "19690022940")),
    ("A_design_basis", "Stochl1970_gaseous_helium_requirements_LH2_discharge",
     ("ntrs", "19710004571")),
    ("A_design_basis", "Tomsik2000_LOX_densification_unit_X33",
     ("ntrs", "20050203875")),
    # A4 -- the Centaur primary sources, located from Baldwin2023's reference list [4],[5].
    ("A_design_basis", "Lacovic1970_centaur_LOX_tank_helium_requirements",
     ("ntrs", "19700018327")),
    ("A_design_basis", "Johnson1967_helium_pressurant_LH2_submerged_gas_injection",
     ("ntrs", "19670024112")),
    # Located from Ramesh2014 reference [3].
    ("A_design_basis", "Cleary1995_simplified_LOX_propellant_conditioning_concepts",
     ("ntrs", "19950018138")),
    ("A_design_basis", "Boeing2002_LO2_densification_without_rotating_machinery",
     ("url", "https://danahercryo.com/wp-content/uploads/2022/07/"
             "Boeing-Densification-Paper_6.2002-3599.pdf")),

    # --- Tier B: model basis --------------------------------------------------
    ("B_model_basis", "Baldwin2023_nodal_submerged_helium_injection",
     ("ntrs", "20220008221")),
    # NTRS holds only the conference abstract (.docx) for this one, not the full paper.
    ("B_model_basis", "NASA2023_single_multi_node_direct_submerged_self_pressurization_ABSTRACT",
     ("raw", "https://ntrs.nasa.gov/api/citations/20230008395/downloads/multi-node_pressurization_abstract_AIAA.docx")),
    ("B_model_basis", "Majumdar2024_nodal_modeling_feed_pressurization",
     ("ntrs", "20240003493")),
    # Open access (CC BY-NC-ND) but nature.com requires an auth cookie for the PDF and both
    # PMC PDF endpoints return HTML to non-browser clients. Europe PMC serves the full JATS XML,
    # which carries the complete body text, tables and equations -- that is what we archive.
    ("B_model_basis", "Chung2025_cryogenic_helium_subsurface_pressurization.fulltext",
     ("raw", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12264134/fullTextXML")),

    # --- Tier C: correlations & properties ------------------------------------
    ("C_correlations", "Balasubramaniam2006_two_phase_flow_reduced_gravity",
     ("ntrs", "20060008906")),
    ("C_correlations", "Subramanian_convective_mass_transfer_notes",
     ("url", "https://lin-web.clarkson.edu/projects/subramanian/ch330/notes/"
             "Convective%20Mass%20Transfer.pdf")),

    # --- Tier D: destratification ---------------------------------------------
    # Chollackal/Sutheesh (FMFP 2021, Springer LNME) is paywalled and ResearchGate
    # blocks automated download -- see MANIFEST.md, acquire manually.
    ("D_destratification", "Raibole2025_review_thermal_stratification_cryogenic_tanks",
     ("url", "https://dergipark.org.tr/en/download/article-file/5350785")),

    # --- Tier E: tools, manuals, baselines ------------------------------------
    ("E_tools_manuals", "Majumdar2016_GFSSP_v6_user_manual",
     ("url", "https://www.nasa.gov/wp-content/uploads/2024/04/gfssp-v6-usermanual.pdf")),
    ("E_tools_manuals", "NASA_GFSSP_v7_supplement_user_manual",
     ("url", "https://www.nasa.gov/wp-content/uploads/2024/04/"
             "gfssp-v7-supplementtousermanual.pdf")),
    ("E_tools_manuals", "Majumdar2011_GFSSP_v6_general_purpose_thermofluid",
     ("ntrs", "20110015752")),
    ("E_tools_manuals", "NASA2017_self_pressurization_flightweight_LH2_tank",
     ("ntrs", "20170001292")),
    ("E_tools_manuals", "Vanoverbeke2010_history_collapse_factor_modeling",
     ("ntrs", "20100026018")),
    ("E_tools_manuals", "NASA2019_validated_prediction_collapse_factor",
     ("ntrs", "20190030454")),
]


def _open(url: str, timeout: int = 90):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=timeout)


def resolve_ntrs(doc_id: str) -> list[str]:
    """Return candidate PDF URLs for an NTRS document id, best first."""
    candidates: list[str] = []
    api = f"https://ntrs.nasa.gov/api/citations/{doc_id}"
    try:
        with _open(api, timeout=45) as resp:
            meta = json.loads(resp.read().decode("utf-8", "replace"))
        for dl in meta.get("downloads", []):
            link = (dl.get("links") or {}).get("pdf") or (dl.get("links") or {}).get("original")
            if link:
                if link.startswith("/"):
                    link = "https://ntrs.nasa.gov" + link
                candidates.append(link)
    except Exception as exc:  # noqa: BLE001 - fall through to the guessed URL
        print(f"    [api] {type(exc).__name__}: {str(exc)[:120].encode('ascii', 'replace').decode()}")
    # Conventional fallbacks used across the NTRS corpus
    candidates.append(f"https://ntrs.nasa.gov/api/citations/{doc_id}/downloads/{doc_id}.pdf")
    candidates.append(f"https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/{doc_id}.pdf")
    seen, ordered = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


def _curl(url: str, dest: Path) -> tuple[bool, str]:
    """Fallback for hosts whose certificate chain the Python trust store rejects."""
    import subprocess
    cmd = ["curl", "-sSL", "--max-time", "300", "-A", UA, "-o", str(dest), url]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not dest.exists():
        return False, f"curl rc={proc.returncode} {proc.stderr[:80]}"
    if dest.read_bytes()[:4] != b"%PDF":
        dest.unlink(missing_ok=True)
        return False, "curl fetched non-PDF"
    return True, f"{dest.stat().st_size / 1024:.0f} KB (curl)"


def download(url: str, dest: Path, expect_pdf: bool = True) -> tuple[bool, str]:
    try:
        with _open(url) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        if "CERTIFICATE" in str(exc).upper() and expect_pdf:
            return _curl(url, dest)
        return False, f"{type(exc).__name__}: {str(exc)[:120].encode('ascii', 'replace').decode()}"
    if expect_pdf and not data.startswith(b"%PDF"):
        raw = data[:80].decode("utf-8", "replace").replace("\n", " ")
        head = "".join(c if 32 <= ord(c) < 127 else "." for c in raw)
        return False, f"not a PDF ({len(data)} B, starts {head!r})"
    dest.write_bytes(data)
    return True, f"{len(data) / 1024:.0f} KB"


def main() -> int:
    results: list[tuple[str, str, str, str]] = []
    for tier, key, (kind, spec) in REFS:
        if kind == "raw":
            ext = ".docx" if spec.endswith(".docx") else ".xml"
        else:
            ext = ".pdf"
        dest = HERE / tier / f"{key}{ext}"
        if dest.exists() and dest.stat().st_size > 4096:
            print(f"[skip] {key} ({dest.stat().st_size / 1024:.0f} KB already present)")
            results.append((tier, key, "open", f"{dest.stat().st_size / 1024:.0f} KB"))
            continue

        print(f"[get ] {key}")
        urls = resolve_ntrs(spec) if kind == "ntrs" else [spec]
        ok, note = False, "no candidate url"
        for url in urls:
            ok, note = download(url, dest, expect_pdf=(kind != "raw"))
            print(f"    -> {'OK  ' if ok else 'FAIL'} {note}  <- {url[:110]}")
            if ok:
                break
        results.append((tier, key, "open" if ok else "FAILED", note))

    print("\n" + "=" * 78)
    got = [r for r in results if r[2] == "open"]
    lost = [r for r in results if r[2] != "open"]
    print(f"downloaded/present: {len(got)}/{len(results)}")
    for tier, key, _, note in lost:
        print(f"  MISSING  {tier}/{key}  ({note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
