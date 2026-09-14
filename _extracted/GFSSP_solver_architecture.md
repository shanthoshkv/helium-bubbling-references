# Extracted solver architecture — GFSSP

Sources held locally: `Majumdar2011_GFSSP_v6_general_purpose_thermofluid.pdf` (34 pp, TFAWS 2011
overview — the compact statement), `Majumdar2016_GFSSP_v6_user_manual.pdf` (NASA/TP-2016-218218,
885 pp), `NASA_GFSSP_v7_supplement_user_manual.pdf`. We are re-implementing this architecture in
SciPy, not calling GFSSP.

## Discretization

Finite volume over **nodes / branches / conductors**. Scalars (pressure, temperature, species
concentration, mass) live at nodes; mass flow rates and heat transfer rates live at branches and
conductors. Nodes are either **internal** (solved) or **boundary** (imposed).

## Mathematical closure — 6 unknowns, 6 equations

| Unknown | Equation |
|---|---|
| Pressure | Mass conservation |
| Flow rate | Momentum conservation |
| Fluid temperature | Energy conservation, fluid |
| Solid temperature | Energy conservation, solid |
| Species concentrations | Species mass-fraction conservation |
| Mass | Thermodynamic equation of state |

Reproduce this table in `nodal_tank_model.py`'s docstring. It is the checklist that tells you the
system is closed — a missing equation here is the most common way a hand-rolled tank model ends up
under-determined and quietly non-conservative.

## Energy formulation — three options, and which one this tool needs

- **Temperature option** — energy in terms of `T`. Gas mixtures only.
- **Enthalpy option 1** — mixture enthalpy equation, then `T` recovered iteratively (Newton–Raphson)
  from `Σ_k x_i,k h_i,k(p_i, T_i) − h_i = 0`.
- **Enthalpy option 2 — SEEIS (Separate Energy Equation for Individual Species)** — a separate
  energy equation per species. **Required for liquid–gas mixtures with phase change.**

> **Why this matters here, in GFSSP's own words:** earlier mixture capability could not handle
> phase change in any constituent, *because the mixture energy equation was solved in terms of
> temperature*; to compute phase change, the energy equation for each species must be solved in
> terms of enthalpy or entropy. The worked example given is exactly our problem class —
> "during purging of liquid oxygen by ambient helium, a mixture of helium, LO2 and GO2 exist."
>
> **Therefore: this tool's tank model is enthalpy-based per species (He, GO2, LOX), not
> temperature-based.** Choosing temperature as the state variable would silently forbid the phase
> change that is the entire point of the model.

### Enthalpy option 1 — mixture enthalpy (the form to port)

```
              Σ_j Σ_k x_j,k h_j,k · MAX(−ṁ_ij, 0)  +  (m h_i)_τ / Δτ  +  Q̇_i
h_i,τ+Δτ  =  ------------------------------------------------------------------
              Σ_j Σ_k x_j,k       · MAX( ṁ_ij, 0)  +   m_τ / Δτ
```

### Enthalpy option 2 — SEEIS

```
  ( m_i h_ik − p/(ρ_k J) )_τ+Δτ − ( m_i h_ik − p/(ρ_k J) )_τ
  ----------------------------------------------------------
                          Δτ
      = Σ_j [ MAX(−ṁ_ij, 0) h_jk − MAX(ṁ_ij, 0) h_ik ]  +  Q̇_ik  +  {± Q̇_1→2^HES}
        \_______________ advection ________________/       source    interphase source
```

The `MAX(±ṁ, 0)` pair is **first-order upwinding**: a node receives the donor node's enthalpy.
Implement it exactly this way — it is unconditionally bounded, and the alternative (central
differencing) will produce unphysical over/undershoot when a branch reverses during draining.
`Q̇_1→2^HES` is the interphase source term; **for us that is the bubble mass/heat transfer** —
i.e. the `ṁ_O2` and `Δḣ` terms from Baldwin's Eqs. 2 and 6 enter here.

## Properties

Per species, from node pressure and species enthalpy:
`T_ik, ρ_ik, μ_ik, K_ik, c_p,ik = f(p_i, h_ik)`.
Nodal mixture properties by concentration-weighted average:
`ρ_i = Σ_k c̄_ik ρ_ik`, `μ_i = Σ_k c̄_ik μ_ik`.
Nodal temperature is averaged on **molar** concentration. GFSSP notes an alternative based on
vapour–liquid equilibrium for multi-component multi-phase mixtures was still "in progress" as of
v6 — i.e. **the concentration-averaged nodal temperature is a known approximation, not exact.**
Record that as a stated limitation rather than presenting the ullage temperature as rigorous.

`(p, h) → T` inversion is the hot path. Cache it; `fluid_properties.py` builds its interpolant
over the `(p, h)` box, not `(p, T)`.

## Solver

Hybrid **Newton–Raphson + successive substitution**. Pressures and flow rates go to Newton (they
are strongly coupled and the Jacobian is worth forming); properties, enthalpies and the `(p,h)→T`
inversion go to successive substitution. Do not put everything in one Newton solve — a branch
that chokes or a node that flips phase makes that Jacobian discontinuous.

## Regulator / target-pressure control — the pattern to reuse

Baldwin's submerged-injection cases must **iterate the helium flow rate until the target ullage
pressure is met**. GFSSP solves the analogous problem for a pressure regulator by adjusting flow
area once per time step, with relaxation and clipping. Adapt the **forward-differencing
(Schallhorn–Hass)** form, which is better behaved than a naive secant:

```
A_new     = A_τ · (p_reg/p_τ)^3 · exp( p_reg/p_τ − 1 )
A*_τ+Δτ   = clip( A_τ + η_relax · (A_new − A_τ),  0,  A_max )
```

The backward-differencing (Schallhorn–Majumdar) alternative estimates the sensitivity numerically:

```
A_new = A_τ − (∂A/∂p)(p_τ − p_reg),      ∂A/∂p ≈ |(A_τ − A_τ−Δτ) / (p_τ − p_τ−Δτ)|
```

For our controller, substitute helium mass flow for area. The cubic-times-exponential form gives
strong correction when far from target and gentle correction when close, and `η_relax` plus the
clip keep it from ringing. **Expose `η_relax` and `ṁ_He,max` as inputs, and report the pressure
tracking error each step rather than assuming the controller converged.**

## Scope note

GFSSP v6 ships 25 flow-resistance and 33 fluid options, conjugate heat transfer, a pressure
regulator, prescribed-flow option and a 2-D Navier–Stokes solver. **We reimplement only the
sliver this tool needs**: the tank-pressurization node set from Baldwin (B1) — ullage node,
liquid node, pseudo-boundary node, helium supply node, drain branch to the engine boundary — with
SEEIS-style per-species enthalpy and the interphase source term supplied by our bubble model.
Everything else is out of scope and should stay out.
