# Extracted governing equations — Baldwin, Majumdar & LeClair (AIAA 2023-0847)

`source_id: Baldwin2023_nodal_submerged_helium_injection` · NTRS 20220008221 · local PDF in
`references/B_model_basis/`. Equation numbers below are the paper's own numbering and are the
strings to put in `@sourced(..., eq="Eq. N")` provenance tags.

## Nomenclature as used by the paper (adopt verbatim to keep provenance checkable)

`c_p` isobaric specific heat [kJ/kg/K] · `h` enthalpy [kJ/kg] · `h_g` saturated vapor enthalpy ·
`h_fg` enthalpy of vaporization · `m_LOx` propellant mass [kg] · `m_u` ullage mass [kg] ·
`ṁ_drain` propellant drain rate [kg/s] · `ṁ_vent` ullage vent rate [kg/s] · `ṁ_He` inlet helium
injection rate [kg/s] · `ṁ_ev` boil-off mass transfer rate [kg/s] · `ṁ_O2` diffusional mass
transfer rate [kg/s] · `P_O2`, `P_He` partial pressures [kPa] · `P_u` ullage pressure [kPa] ·
`Q̇` ullage-to-propellant heat transfer rate [W] · `Q̇_leak` heat leak [W] · `R` specific gas
constant [kJ/K/kmol] · `T_He,in` injected helium temperature [K] · `T_prp` propellant temperature
[K] · `T_sat` saturation temperature [K] · `V̇` volumetric flowrate [m³/s] ·
`ΔT_sub` propellant subcooling [K] · `ε_sub`, `ε_cons` errors [-].

## Node network (Section II, Figs. 5–6)

```
ullage node  --(pseudo-boundary node)--  liquid propellant node  --(drain branch)--> engine boundary
      ^                                          ^
      |                                          |
 (direct-injection branch)              (submerged-injection branch)
      |                                          |
   helium supply / boundary node ----------------+
```

The **pseudo-boundary node "serves no physical purpose"** — it exists solely to keep the ullage
and liquid nodes from mixing homogeneously, which a homogeneous flow-network solver would
otherwise do. The connecting branch is the ullage–liquid interface. Implement it, and comment it
with exactly this reason.

## Equations

**(1) Boil-off mass transfer driven by ullage→liquid heat transfer**

```
ṁ_ev = Q̇ / ( h_fg + c_p (T_sat − T_prp) )
```

**(2) Sensible enthalpy delivered to the liquid by the warm helium**
The bubble is assumed to cool *instantly* to the surrounding propellant temperature.

```
Δḣ = ṁ_He · c_p,He · ( T_He,in − T_prp )
```

**(3) Dalton's law closure on the rising bubble**
Total bubble pressure equals the ullage pressure at the moment it merges with the ullage; the
oxygen partial pressure equals the **saturation pressure at the bulk liquid temperature** —
this is the instantaneous-diffusion assumption.

```
P_u = P_O2 + P_He        with  P_O2 = P_sat(T_prp)
```

> **Hydrostatic head finding (important, and it contradicts a plausible-sounding assumption):**
> the authors ran the model twice, once with `P_u` on the LHS of Eq. 3 and once with the
> hydrostatic head added, and found the difference in subcooling and oxygen evaporation to be
> **less than one ten-thousandth of a percent at any time step**. Hydrostatic head is therefore
> negligible *for the tank-level mass-transfer rate*. (It still sets the bubble's local volume
> along the rise path, which is a Tab-1/Tab-2 concern, not a Tab-3 one.) GFSSP still accounts for
> hydrostatic pressure in the conservation equations; it is omitted only in the user mass-transfer
> subroutine.

**(4), (5) Ideal-gas equations of state for the two bubble species**
Valid below the gas critical point.

```
ṁ_He = P_He · V̇ / ( R_He · T_He )
ṁ_O2 = P_O2 · V̇ / ( R_O2 · T_O2 )
```

**(6) Equilibrium-model diffusional mass transfer — the core closure**

```
ṁ_O2 = ( P_O2 · R_He ) / ( P_He · R_O2 ) · ṁ_He
```

Mass transfer rate is driven by helium injection rate, ullage pressure, and liquid propellant
temperature. Note the structure: `P_O2 = P_sat(T_prp)` is largest when the liquid is warmest, so
the mass-transfer rate is highest at the start of a run and decays as the liquid subcools. This
is the same self-limiting mechanism the GSLV flight paper (A1) invokes to explain the slow LOX
temperature rise late in the burn.

**(7), (8) Liquid propellant node — mass and enthalpy-based energy, with draining**

```
m_LOx^t − m_LOx^(t−Δt) = −( ṁ_O2 + ṁ_ev ) Δt − ṁ_drain Δt

[ m(h − P/ρ) ]_LOx^t − [ m(h − P/ρ) ]_LOx^(t−Δt)
------------------------------------------------ =
                     Δt
      ṁ_He c_p,He ( T_He,in − T_prp^t )
    − ( ṁ_O2 + ṁ_ev ) h_g,O2
    − ṁ_drain h_LOx^t
    + Q̇_leak + Q̇
    + ( P ΔV/Δt + V ΔP/Δt )
```

Term-by-term (the paper's own reading): (i) enthalpy gained from the warm helium; (ii) energy
consumed vaporizing propellant during mass transfer — thermal energy from the liquid drives the
phase change, and **this is the subcooling term**; (iii) enthalpy leaving with the drain;
(iv) heat leak; (v) ullage→liquid heat transfer; (vi) work done by the ullage on the liquid via
drain, evaporation, boil-off and pressurization (negligible in a no-drain case).

**(9), (10) Ullage node — mass and energy**

```
m_u^t − m_u^(t−Δt) = ( ṁ_O2 + ṁ_ev + ṁ_He − ṁ_vent ) Δt

[ m(h − P/ρ) ]_u^t − [ m(h − P/ρ) ]_u^(t−Δt)
--------------------------------------------- =
                    Δt
      ( ṁ_O2 + ṁ_ev ) h_g,O2
    + ṁ_He h_He
    − ṁ_vent h_u
    + Q̇_leak − Q̇
    − ( P ΔV/Δt + V ΔP/Δt )
```

Venting terms drop out when the ullage is not vented.

**Species bookkeeping:** GFSSP applies a mass sink + species-concentration sink in the liquid
node and a matching mass source + species source in the ullage node. In this single-fluid
formulation the rate of helium entering the liquid equals the rate entering the ullage, i.e.
**net zero change in helium mass held in the liquid** — dissolved helium is *not* modeled here.
That is precisely the gap the Zimmerli solubility term (B11) is meant to close, and the paper's
own future-work section names "pressurant dissolution into the liquid propellant" as unfinished.

**(11), (12) Non-drained variants** (Cho's apparatus has no drain line)

```
m_LOx^t − m_LOx^(t−Δt) = −( ṁ_O2 + ṁ_ev ) Δt

[ m(h − P/ρ) ]_LOx^t − [ m(h − P/ρ) ]_LOx^(t−Δt)
------------------------------------------------ =
                     Δt
      ṁ_He c_p,He ( T_He,in − T_prp^t ) − ( ṁ_O2 + ṁ_ev ) h_g,O2 + Q̇_leak + Q̇
```

**(13), (14), (15) Metrics**

```
ΔT_sub  = T_initial − T_final
ε_sub   = ( ΔT_sub,sim − ΔT_sub,exp ) / ΔT_sub,exp
ε_cons  = ( m_cons,sim − m_cons,exp ) / m_cons,exp
```

Positive ε means the simulation **over**predicted.

## Solution procedure worth copying

- Cho (non-drained) cases: initial ullage pressure and helium injection rate are known, so
  Eqs. 1–6 are closed and solved directly.
- Centaur submerged cases: helium inlet temperature and pressure are fixed; the target ullage
  pressure must be met, so **an initial guess for the helium flowrate is made and Eqs. 1–10 are
  solved iteratively until the target ullage pressure is reached.** The submerged case is harder
  than the direct case precisely because injecting beneath the surface couples the pressurant
  flow to the diffusional mass transfer.
- Ullage→wall and ullage→liquid heat transfer use **standard flat-plate natural-convection
  correlations** (paper's ref. [6] = Ring, *Rocket Propellant and Pressurization Systems*,
  Prentice-Hall 1964), with a user-applied adjustment factor on the heat transfer coefficient.

## Findings this tool must reproduce or respect

1. **±30 % is the honest bound.** "Validated against two sets of experimental data and shown to
   predict both propellant subcooling and helium consumption to within 30 % in most cases."
   Cho cases 9 and 10 are the exceptions at −63 % and −70 % — and both are cases where the liquid
   *warmed* (ΔT_sub < 0), i.e. the metric itself is ill-conditioned near zero subcooling. A tool
   reporting % error on near-zero subcooling must say so rather than print a giant number.
2. **The instantaneous model overpredicts subcooling** in almost all cases — "the expected result
   in accordance with the idealized model." Final liquid temperatures never deviate more than
   **3 %** from test data even where ΔT_sub error is large. Report both metrics; ΔT_sub error
   alone overstates how wrong the model is.
3. **Baldwin concludes a finite-rate model is *not* necessary** — "the complexity of the physics
   and its associated uncertainties would serve to reduce the error by few percent." This is a
   direct counterweight to Cho's own finite-rate framing, and both belong in the tool's closure
   selector so the user can see the difference rather than being told which is right.
4. **Default GFSSP heat transfer underpredicts helium consumption in every Centaur case** →
   the default model is a defensible **lower bound** on helium usage. Tripling the ullage-to-wall
   and ullage-to-liquid HTCs (adding an effective forced-convection component, since helium enters
   near the top and flows along the walls) brings most cases inside 30 %, and direct-injection
   cases inside 6 % in all but one. **The tool must expose this HTC multiplier as a first-class
   input with the default = 1.0 and a documented 3.0 "forced-convection-corrected" setting.**
5. **Submerged injection uses about half the helium of direct injection** at similar operating
   conditions (compare Table 7/8 direct vs. Table 10 submerged), *plus* it subcools the propellant.
   That is the headline design result for Tab 5.
6. **Design guidance for the sparger:** heat-transfer assumptions are best where rising bubbles
   reach thermal equilibrium with the liquid, so tanks designed for **increased bubble residence
   time** and **smaller-diameter bubbles** are recommended — smaller bubbles also make the mass
   transfer assumption better. Reducing the liquid/pressurant injection temperature difference
   shortens the time to equilibrium. Feed this straight into the Tab 4 sparger optimizer.
7. **Low-g caveat:** the mass transfer formulation is gravity-independent, but in low-g the
   residence time rises greatly and **bubbles may not reach the ullage at all** because buoyancy
   is reduced. Higher-g shortens residence time and increases the error of instantaneous models.

## Reference chain resolved from this paper

- **Cho's papers are both 2006, not 2005**: *Cryogenics* 46(2-3):132–142 and 46(11):778–793.
- **Centaur data source located**: Lacovic, R. F., "Comparison of experimental and calculated
  helium requirements for pressurization of a Centaur liquid oxygen tank," NASA E-5539 (1970) —
  this is the Tier-A item A4. Companion: Johnson, W. R., "Helium pressurant requirements for
  liquid-hydrogen expulsion using submerged gas injection" (1967).
- Heat transfer correlations: Ring, E. (ed.), *Rocket Propellant and Pressurization Systems*,
  Prentice-Hall, 1964.
- Hansen, H. C., "Technology Demonstration Mission (TDM) Cryogenic Fluid Management (CFM
  Portfolio) Project: CFM Modeling Portfolio Plan" (2021).
