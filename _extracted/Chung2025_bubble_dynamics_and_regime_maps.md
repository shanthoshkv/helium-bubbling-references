# Extracted correlations and data — Chung et al., *npj Microgravity* 11:42 (2025)

`source_id: Chung2025_cryogenic_helium_subsurface_pressurization` · DOI 10.1038/s41526-025-00504-w ·
open access (CC BY-NC-ND) · local full-text JATS XML in `references/B_model_basis/`.
**This is the open-access backbone for Tab 1 (single-bubble physics).** Everything below is
transcribed from the article body and tables — no digitization, so these are exact.

---

## 1. Apparatus (Methods)

| Item | Value |
|---|---|
| Tank | **8.34 L, 20.3 cm dia × 30.5 cm tall**, cylindrical, LN2 |
| Orifices | **0.25 mm** or **1.0 mm**, submerged near the tank bottom |
| View port | 8 cm tall × 6 cm wide, side wall, aligned with the injector |
| Thermocouples | 10 × Omega type-T on a rack; min. horizontal nozzle-to-rack separation **5.1 cm** |
| Pressure | Omega absolute transducer, 0–345 kPa (0–50 psia) |
| He temperature control | shell-and-tube HX, **1.27 cm dia × 25 cm tube**, LN2 on the shell side → **170–260 K** injection |
| Flow control | FC1 covers 2.73×10⁻⁹–2.73×10⁻⁷ kg/s (1–100 sccm); FC2 up to 8.18×10⁻⁶ kg/s (3000 sccm) |
| Imaging | 1000 fps; pixel scale **0.052 mm/px**; bubble-diameter uncertainty **2 px = 0.104 mm**; time uncertainty 0.001 s |
| Gravity | parabolic flight, **0.025–0.064 g_e**, plus Martian and Lunar points, plus 1-g ground |

---

## 2. Correlations (paper equation numbers — use these strings in `@sourced` tags)

### Dimensionless groups (Payne et al., paper Eqs. 1–2)

```
Fr* = [ ρ_g v_g² / ( (ρ_l − ρ_g) g D ) ]^(1/2)          (1)   modified Froude, gas inertia vs. buoyancy
Bo  =   (ρ_l − ρ_g) g D² / σ                             (2)   Bond, gravity vs. surface tension
```

`D` is the orifice diameter, `v_g` the gas velocity at the orifice. Physical roles the paper
states explicitly and which the regime logic must respect: **inertia stabilizes the jet, gravity
collapses the jet, surface tension destabilizes the jet.**

### Jet-transition correlations (paper Eqs. 3–6) — `H` is liquid depth

```
H/D = 0.12 · Fr*^0.80                       4 < Fr* < 30,  0.55 < Bo < 10    (3)  steady → pulsating jet
H/D = 0.12 · Fr*^1.23 · Bo^0.80             4 < Fr* < 30,  0.55 < Bo < 4     (4)  pulsating → transient jet
H/D = Fr*^0.65                              1 < Fr* < 10,  4    < Bo < 50    (5)
H/D = 0.794 · Fr* · Bo^0.25 + 2.124         (Sundar et al. 1999)             (6)  bubbling → jetting
```

Eqs. (4) and (5) differ because **gas inertia dominates once Bo > 4**. Eq. (6) was "presumed to
cover all fluids, **however this correlation has yet to be validated against cryogenic liquids**"
— ship it, but flag every call as `confidence: unvalidated-for-cryogens`.

### Bubble departure volume, dynamic regime (paper Eq. 7 — Davidson & Schüler)

```
V_b = (4π/3)^(1/4) · [ 15 μ_l Q / ( 2 (ρ_l − ρ_g) g ) ]^(3/4)
```

with `Q` the volumetric gas flow rate and `μ_l` the liquid viscosity. **This is the departure-diameter
closure for Tab 1 and it is now sourced from an open paper** — it replaces the "pull the exact
correlation from B4" gap for the dynamic (intermediate-flow) regime. Note it has **no surface
tension term**: it is the viscous/dynamic-regime limit, not the quasi-static one. The quasi-static
(low-flow) limit still needs a force-balance form; Buyevich & Webbon (1996) is the correct source
for the reduced-gravity branch and remains unacquired.

### Terminal rise velocity, large bubbles (paper Eq. 8)

```
v_b = 1.05 · [ g D (ρ_l − ρ_g) / ρ_l · ( c_d / 2 ) ]^(1/2)          for d_b > 5 mm
```

Stated validity **d_b > 5 mm only**. Below that, fall back to the Tomiyama/Clift-Grace-Weber
regime set. Enforce the 5 mm switch as a hard branch, not a blend.

### Independent-bubble validity criterion (Wallis)

> "For a volume fraction of gas less than **10 %**, the rate of collision and agglomeration of
> bubbles is usually slow, and for that gas volume fraction range the bubbles can be treated
> independently … single bubble characteristics can be extended to account for the whole bubbling
> system without significant error."

**This is the quantitative licence for the monodisperse single-bubble model, and it is a runtime
check, not a footnote.** `bubble_dynamics.py` must compute the column void fraction and emit a
warning when `α > 0.10`: *"void fraction 0.14 exceeds the Wallis 10 % independent-bubble limit —
coalescence is expected and the monodisperse assumption is outside its stated validity."*

### Lumped-capacity criterion (Cho, via this paper)

Cho used **Bi < 0.1** to justify a lumped heat-capacity bubble model. Compute the bubble Biot
number and report it; if `Bi > 0.1` the lumped bubble energy equation is out of validity.

---

## 3. Measured data

### Table 2 — bubble departure diameter, 1 mm orifice (values ± reported scatter)

| Case | g/g_e | ṁ_He, kg/s | T_He, K | ρ_He, kg/m³ | **BDD, mm** |
|---|---|---|---|---|---|
| 3-1 | 0.027 | 2.73e-9 | 208 | 0.2317 | 7.14 ± 1.71 |
| 3-2 | 0.047 | 2.73e-9 | 218 | 0.2207 | 7.98 ± 1.95 |
| 3-3 | 0.041 | 2.73e-9 | 230 | 0.2088 | 9.43 ± 0.19 |
| 3-4 | 0.064 | 2.73e-9 | 230 | 0.2088 | 8.37 ± 0.27 |
| 3-5 | 0.044 | 2.73e-8 | 198 | 0.2438 | 6.12 ± 0.13 |
| 3-6 | 0.043 | 2.73e-8 | 200 | 0.2413 | 6.30 ± 0.20 |
| **3-7** | **1** | 2.73e-9 | 260 | 0.1841 | **3.80 ± 0.24** |
| **3-8** | **1** | 2.73e-8 | 214 | 0.2250 | **4.02 ± 0.09** |
| **3-9** | **1** | 2.73e-7 | 240 | 0.1998 | **4.74 ± 0.38** |

**Cases 3-7 to 3-9 are the 1-g validation set for the departure model (validation case 9).**
The low-g cases are for the deferred g-toggle. 1-g BDD ≈ 3.8–4.7 mm at a 1 mm orifice in LN2;
low-g BDD ≈ 6.1–9.4 mm at the same flow rates — **roughly 50–100 % larger**, because with
buoyancy suppressed, surface tension controls detachment.

### Table 3 — flow regime vs. mass flow rate (units 1×10⁻⁹ kg/s)

| Condition | Bubbly | Slug | Jet |
|---|---|---|---|
| 1-g, 0.25 mm | 2.73–27.3 | 273 | 2730–8180 |
| Low-g, 0.25 mm | 2.73–27.3 | 273 | 2730–8180 |
| 1-g, 1 mm | 2.73–27.3 | 2730–8180 | — (not observed) |
| Low-g, 1 mm | 2.73–27.3 | 2730–8180 | — (not observed) |

**Jet flow never appears at the 1 mm orifice** in either gravity. Regime maps: 1-g uses `Bo`–`Fr`
(gravity-dominated); reduced-g uses **Suratman number `Su` and `Re`** per Balasubramaniam (C9),
because gravity is no longer an influencing factor and the regime becomes essentially a function
of `Re` alone.

### Table 4 — cooling rate and effectiveness (low-g)

| ṁ_He, kg/s | ΔT, K | period, s | cooling rate, K/s | **effectiveness, K/g** |
|---|---|---|---|---|
| 2.73e-9 | 0.172 | 43.4 | 0.0040 | **1465.2** |
| 2.73e-8 | 0.214 | 43.4 | 0.0050 | **183.2** |
| 2.73e-7 | 0.338 | 50.3 | 0.0067 | **24.5** |
| 2.73e-6 | 0.359 | 52.9 | 0.0068 | **2.5** |
| 8.18e-6 | 0.507 | 36.7 | 0.0138 | **1.7** |

> **The central design tension of the whole tool, quantified.** Cooling *rate* rises with helium
> flow (and is non-linear in it); cooling *effectiveness* — cooling per gram of helium spent —
> falls **~900×** across this range and is inversely proportional to mass flow. Mechanism: rising
> flow raises `Re_g`, pushing bubbly → slug → jet, and heat/mass transfer is highest in bubbly
> flow because it has the largest interfacial area per unit gas volume.
>
> **Tab 5 must optimize on effectiveness, not rate.** A design that maximizes subcooling rate
> maximizes helium bottle mass, which is exactly the thing submerged injection exists to reduce.
> Ramesh (A3) reports higher flow → more cooling and Chung reports higher flow → worse
> effectiveness; these are not in conflict, they are the two axes of the same trade, and the tool
> should plot them together on one chart.

### Table 5 — measurement uncertainties (feed straight into the UQ tab defaults)

| Variable | Value | Uncertainty |
|---|---|---|
| D_tube, mm | 16.00 | 0.12 |
| T_i, K | measured (TC) | 1.00 |
| T_l, K @ 101.3 kPa | 77.34 | 0.29 |
| T_l, K @ 122.0 kPa | 78.97 | 0.50 |
| μ_l, µPa·s @ 101.3 kPa | 160.66 | 1.79 |
| μ_l, µPa·s @ 122.0 kPa | 150.90 | 2.90 |
| ρ_l, kg/m³ @ 101.3 kPa | 806.08 | 1.29 |
| ρ_l, kg/m³ @ 122.0 kPa | 798.72 | 2.30 |
| ṁ_He | measured (MFC) | **0.02 %** |
| P, kPa | measured (PT) | 0.28 |

---

## 4. Findings to encode

1. **Same three closure cases as Ramesh (A3), independently named**, with the sources attributed:
   case 1 instantaneous heat + mass (→ Baldwin B1, max achievable subcooling, "useful for initial
   design studies"); case 2 finite heat + instantaneous mass (→ Cho B5); case 3 finite heat and
   mass (→ Saha & Sandilya B6). **Three independent papers converge on the same taxonomy — the
   tool's closure selector should use exactly these three names.**
2. **Cho's justification for case 2, recorded here:** bubbles injected into a LOX tank are unlikely
   to reach thermal equilibrium in small tanks or in upper-stage pipes, and Cho *measured* the
   ullage temperature rising during injection, which is direct evidence of thermal
   non-equilibrium. So case 2, not case 1.
3. **Larger interfacial area helps cooling, but raising bubble population backfires**: collisions
   merge bubbles and cut surface area abruptly. Restrict the population. Combined with the Wallis
   10 % criterion this gives Tab 4 a hard, defensible constraint — *maximize orifice count at
   fixed total flow until α approaches 0.10, then stop.*
4. **Bubble-formation regime sequence** (Badam et al.): single bubbling → coalescence at the
   orifice / pairing above it → triple → quadruple → chaotic. Lifting forces = buoyancy + pressure
   + gas momentum; restraining = surface tension + drag + inertia. Transition to chaotic occurs as
   `Fr` rises (higher gas velocity or smaller orifice) at fixed `Bo`. For very small orifices the
   transition goes **straight from single bubble to chaotic**, skipping the intermediate regimes.
5. **Low-g:** bubble formation time is longer (reduced buoyancy keeps the bubble attached), and the
   same regime transition needs a mass flow **two orders of magnitude higher in 1-g than in low-g**.
   Largest post-departure size fluctuations belong to the largest (~9 mm) bubbles, because surface
   tension controls shape and its restoring effect weakens with size; the coldest helium (208 K)
   gave the smallest fluctuation amplitude.
6. Liquid depth is **not** a significant factor above ~2.5 cm at low gas injection velocity
   (Davidson & Amick; Hayes et al.), though this was never confirmed at high injection velocity.
   Useful: the Ramesh and Cho Dewars are both far above that threshold, so depth need not be a
   tuning parameter when matching them.

## 5. New references located from this paper

| Item | Use | Status |
|---|---|---|
| Payne et al. — modified Froude and Bond numbers for jet transition | Eqs. 1–2 origin | paywalled; forms transcribed above |
| Sundar et al. (1999) — momentum-exchange transition model | Eq. 6 | paywalled |
| **Davidson & Schüler (1960)** — dynamic-regime bubble volume | **Eq. 7, Tab 1 core** | paywalled; **form transcribed above, so not blocking** |
| Badam et al. — bubble formation regimes at submerged orifices | regime sequence, force balance | paywalled |
| Zhang & Shoji — nonlinear bubble interaction model | not implemented (validity not established) | paywalled |
| Wallis (1969), *One-Dimensional Two-Phase Flow* | 10 % void-fraction independence criterion | book |
| Frederking & Clark (1962), *Adv. Cryo. Eng.* 8:501–506 | film-boiling interface correlation Cho compared against | paywalled |
| Balasubramaniam et al., NASA/CR-2006-214085 | low-g regime map, Su–Re coordinates | **held locally** (C9) |
| Miyahara et al.; Spells & Bakowski; Quigley et al.; Davidson & Amick; Hayes et al.; Tufaile et al.; Delnoij et al. | supporting regime literature | not required for v1 |
