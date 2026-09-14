# Extracted test data and model — Ramesh & Thyagarajan (IJET 6(1), 2014), LPSC Mahendragiri

`source_id: Ramesh2014_subcooling_cryogenic_liquids_helium_bubbling` · open access · local PDF in
`references/A_design_basis/`. **Validation case 5 — the primary quantitative case that is
actually obtainable.** ISRO/LPSC hardware, same organisation as A1/A2.

## Apparatus (exact, from Section III)

| Item | Value |
|---|---|
| Vessel | Super-insulated Dewar, **1000 L** |
| Inner vessel | **900 mm dia × 1030 mm shell height**, semi-elliptical dishes top and bottom |
| Insulation vacuum | 1 × 10⁻⁴ mbar |
| Instrumentation | 4 × RTD, axial distribution; pressure transducer; DP transmitter on He supply |
| **Sparger** | **4 submerged nozzles, each with 10 holes of 2 mm diameter** → `N_o = 40`, `d_o = 2 mm` |
| Flow control | helium volume flow held constant; rate varied by changing upstream supply pressure |
| **Measured heat in-leak** | **220 W** (back-computed from LN2 warm-up at saturated ambient condition) |
| Fill level | 90 % of tank |
| LN2 saturation reference | 77.36 K at 1.0 bar(a) |

This is a complete, self-consistent test article: tank geometry, sparger geometry, heat leak,
fill fraction and instrument set are all specified. **Build this as the default worked example
in Tabs 1–3** — it is the only design-basis case where every input needed is published.

## Test matrix (Tables 1–3)

| Liquid | System pressure | He flow rate | He injection temperature |
|---|---|---|---|
| LN2 | 1.0 bar(a) | 15, 20, 25 g/s | 85, 150, 295 K |
| LOX | 1.0 bar(a) | 15, 20, 25 g/s | 85, 150, 295 K |
| LH2 | 1.0 bar(a) | 30, 35, 40 g/s | 85, 150, 295 K |

85 K and 150 K helium obtained by passing the supply through an LN2 cooler bath.

> ### The stated "1.0 bar,a" is actually 1 atm — load 101325 Pa, not 1e5 Pa
>
> The paper states the Dewar pressure as "1.0 bar,a" **and separately** states that LN2 exists
> saturated at **77.36 K** under that condition. Those two statements are inconsistent by
> CoolProp:
>
> | Pressure | LN2 T_sat | LOX T_sat |
> |---|---|---|
> | 1.00 bar (100 000 Pa) | 77.243 K | 90.062 K |
> | 1 atm (101 325 Pa) | **77.355 K** | 90.188 K |
>
> Their 77.36 K identifies the condition as **ambient atmospheric**, not 1.00 bar — the paper is
> using "bar" loosely for "atmosphere", which is common in test-report prose. The difference is
> only 0.11 K in `T_sat`, but the driving potential of the entire model is
> `P_sat(T_liquid) − p_vapour,bubble`, so a 1.3 kPa error in system pressure is a systematic
> bias on every Ramesh comparison, in the same direction, for the whole run.
>
> **Case-library loader must set `P = 101325 Pa` for all Ramesh cases.** Locked by
> `tests/test_fluid_properties.py::test_ramesh_stated_1_bar_is_really_1_atm`.
>
> Related: the LOX runs start at **90.7 K** against `T_sat(1 atm) = 90.19 K`, i.e. about 0.5 K
> above saturation — consistent with the 220 W standing heat leak warming the bulk before
> bubbling starts. Cho's atmospheric cases likewise start 0.1–1.1 K above saturation. Do not
> initialise these cases *at* saturation; initialise at the published bulk temperature and let
> the model see the real starting superheat.

## Model (Section II) — this is the closure the LPSC line of work actually uses

Total vaporization splits into a heat-driven part and a diffusion-driven part:

```
(1)   ṁ_LN2 = ṁ_LN2,h + ṁ_LN2,diff
(2)   ṁ_LN2 · c_p,LN2 · dT_LN2/dt = Q̇_gi − ṁ_LN2 · h_fg + Q̇_amb
(3)   Q̇_gi = ṁ_LN2,h · h_fg          [the paper prints this as ṁ_LN2 h_fg; by context it is the
                                       heat-driven component only — otherwise (2) is trivial]
```

Substituting (1) and (3) into (2) **cancels the heat-transfer-driven vaporization term entirely**,
leaving the diffusion-driven term as the sole cooling mechanism:

> "Therefore the vaporization due to diffusion `ṁ_LOX,diff` is the main drive for cooling.
> Sub-cooling by helium injection can be characterised by **diffusion-driven evaporative cooling**."

This is an important structural result and a free unit test: **in the L0/L1 energy balance, the
warm-helium sensible term must not appear as a net cooling contribution — it vaporizes liquid and
that vaporization returns its own latent heat. Only the partial-pressure-driven diffusion term
subcools.** Assert it.

### The three limiting closures, named by the source

1. **Instantaneous heat and mass transfer** — bulk liquid and gas always in thermodynamic phase
   equilibrium. **Gives the maximum sub-cooling rate** → this is the L0 upper bound, and it is
   the assumption Baldwin's GFSSP model (B1) uses.
2. **Finite heat transfer + instantaneous mass transfer** — gas and liquid temperatures differ,
   but infinite mass-transfer rate keeps the N2/O2 partial pressure at the 'b' surface equal to
   the bulk gas value. **"Gives satisfactory agreement with experimental data for small bubbles
   and gas with high diffusion coefficient such as helium."** Cho reaches the same conclusion
   independently. **Make this the tool's default closure.**
3. **Finite heat and mass transfer** — most realistic in principle, not needed in practice.

### Closure 2 evaporation rate (paper Eq. 4)

```
              A_s · [ h_gi (T_g − T_i) − h_li (T_i − T_L) ]
   ṁ_L   =   ---------------------------------------------
                              h_fg
```

with `A_s` the net bubble surface area, `T_i` the interface temperature, and `h_gi`, `h_li` the
gas-to-interface and liquid-to-interface heat transfer coefficients. `T_i` is found by requiring
phase equilibrium at the interface (partial pressure of the vapour species in the bubble equals
the saturated vapour pressure of the liquid at `T_i`). **Note the two-film structure — it is the
same skeleton as Xie's two-film model (B7); the tool implements one two-film core and switches
which resistance is set to zero to move between closures 1, 2 and 3.**

## Digitized results (Figs. 5–11)

**Digitization uncertainty: ±0.3 K on temperature, ±50 s on time** (read from printed plots with
gridlines; the paper publishes no tables). Treat as trend data with error bars, per master
prompt §1.5. All runs at 1.0 bar(a), atmospheric-condition tests.

### LOX, helium flow rate sweep (Figs. 5 and 10) — He at ambient temperature
Start temperature 90.7 K.

| ṁ_He, g/s | T at 4000 s, K | approx. ΔT_sub, K | note |
|---|---|---|---|
| 15 | 77.7 | 13.0 | still falling slowly at 4400 s |
| 20 | 76.2 | 14.5 | |
| 25 | **75.0** | **15.7** | paper states "reaches as low as 75 K at 4000 s" |

Trend to reproduce: **higher He flow → more cooling.** Mechanism given by the authors: more
helium raises the He fraction in the bubble and lowers the GO2 fraction, which raises the
liquid-side transfer and the net cooling. Curves flatten after ~3000 s as the driving partial
pressure difference collapses — the same self-limiting behaviour the GSLV flight data shows.

### LOX, helium injection temperature sweep (Fig. 8)
Start 90.7 K.

| T_He, K | final T, K | time, s | approx. ΔT_sub, K |
|---|---|---|---|
| 85 | 75.6 | 4000 | 15.1 |
| 150 | 79.5 | 3600 | 11.2 |
| 295 | 86.2 | 3200 | 4.5 |

### LN2, helium injection temperature sweep (Fig. 7)
Start 78.0 K.

| T_He, K | final T, K | time, s | approx. ΔT_sub, K |
|---|---|---|---|
| 85 | 72.1 | 3000 | 5.9 |
| 150 | 75.0 | 2100 | 3.0 |
| 295 | 76.5 | 2100 | 1.5 |

### LH2, helium injection temperature sweep (Fig. 9) and flow sweep (Fig. 11)
Start 20.3 K. **Both sweeps produce almost no separation** — final temperatures 19.2–20.05 K
across a 210 K span of injection temperature, and 19.2–19.8 K across 30–40 g/s.

> **The LH2 result and its stated cause:** "for Liquid Hydrogen the cooling is unaffected …
> the vaporization due to the vapour side heat transfer and Liquid side heat transfer is more or
> less same." This is an independent, physics-level corroboration of the Stochl (A5) and
> Johnson (A5b) pressurant-penalty result, arrived at from the opposite direction. **The Tab 5
> LH2 warning now rests on three independent sources, not one.**

### Closure comparison (Fig. 6), LOX at 20 g/s
Start 90.7 K, 5000 s:

| Curve | T at 5000 s, K |
|---|---|
| measured | 78.5 |
| calculated, finite heat + instantaneous mass (closure 2) | 78.5 |
| calculated, instantaneous heat and mass (closure 1) | 74.5 |

**The equilibrium closure over-predicts subcooling by ≈4 K out of ≈12 K — a ~33 % overprediction
on ΔT_sub**, which is entirely consistent with Baldwin's finding that his instantaneous GFSSP
model over-predicts (B1: +17 to +19 % on Cho's cases). This single figure is the tool's cleanest
validation of the *closure selector itself*: running closure 1 and closure 2 on this case must
reproduce both curves and the gap between them.

## Design guidance extracted (for Tab 4, sparger optimizer)

- **Nozzle placement pattern matters as much as flow rate.** "Instead of having the nozzles along
  the axis, if placed radially it gives a stirring effect to the bulk liquid and more surface
  area contact takes place. This increases the cooling rate." Circumferential/radial > axial.
  This is the same conclusion the destratification-index literature reaches about orifice
  arrangement (D1/D2), from a different method.
- Cold helium beats warm helium **even at lower mass flow** — the tool's optimizer should trade
  He temperature against He mass, not just maximize flow.
- Saturated liquid subcools more readily than already-subcooled liquid (the driving vapour
  pressure is higher), so subcooling should be applied **after** pre-pressurization, not before —
  otherwise the liquid warms back up during pre-pressurization. Put this in the ops-sequence note.

## New references located from this paper's bibliography

| Item | Why it matters | Status |
|---|---|---|
| Larsen, P. S. & Clark, J. A., "Cooling of cryogenic liquids by gas injection," *Adv. Cryo. Eng.* 8:507–520 (1962) | The LOX companion to Schmidt's LH2 paper (B8); the original MSFC LOX bubbling work | paywalled |
| Cleary, N. L., Holt, K. A. & Fachbart, R. H., "Simplified liquid oxygen propellant conditioning concepts," **NASA TM-108482** | LOX conditioning concepts — NASA TM, should be on NTRS | **fetch** |
| **Buyevich, Yu. A. & Webbon, B. W., "Bubble formation at a submerged orifice in reduced gravity," *Chem. Eng. Sci.* 51(21):4843–4857 (1996)** | **Departure-diameter correlation including the reduced-gravity branch** — exactly the Tab 1 model, and the analytical counterpart to Chung's (B9) measurements | paywalled |
| **Davidson, J. F. & Schüler, B. O. G., "Bubble formation at an orifice in a viscous liquid," *Trans. IChemE* 38 (1960)** | The classical quasi-static departure-diameter correlation | paywalled |
| Han, U. N., "Ground pressurization by helium bubbling for cryogenic upper stages," AIAA 2001-3833 | Directly on-topic prior art | paywalled |
| Wallis, G. B., *One-Dimensional Two-Phase Flow*, McGraw-Hill (1969) | Drift-flux / void fraction | book |
| Panzarella, C. H. & Kassemi, M., "On the validity of purely thermodynamic descriptions of two-phase cryogenic fluid storage," *J. Fluid Mech.* 484:41 (2003) | Bounds when a lumped thermodynamic tank model is legitimate — relevant to justifying the nodal approach | paywalled |
| Reid, R. C. et al., *The Properties of Gases and Liquids*, 4th ed. | Standard source for the Fuller–Schettler–Giddings and Chapman–Enskog diffusivity methods (C4) | book |
