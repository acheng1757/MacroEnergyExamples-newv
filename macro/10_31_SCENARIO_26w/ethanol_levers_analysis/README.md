# Ethanol upgrading: levelized cost plots and lever analysis

Session notes, Nov 2–3 2026. They cover where ethanol goes beyond gasoline blending (diesel, jet, ethylene) across the 10_31_SCENARIO_26w runs, and why.

## 1. Files

| What | Where |
|---|---|
| Liquid-fuel LCOE plot script (gasoline / diesel / jet panels) | `lcoe/liquid_fuels/c_lf_lcoe_by_fuel_plot.py` |
| Ethylene LCOE plot script (reuses the liquid-fuel code) | `lcoe/ethylene/c_ethylene_lcoe_plot.py` |
| Lever table across main cases | `ethanol_levers.py` (this folder) → `ethanol_levers_cases.csv` |
| Lever table across sensitivity sweeps | `sweep_levers.py corn_price\|fixed_om` (this folder) → `sweep_<sweep>.csv` |

This folder lives at `MacroEnergyExamples.jl/macro/10_31_SCENARIO_26w/ethanol_levers_analysis/`. The plot scripts and the `lcoe/...` paths above are in `/Users/abbie/Desktop/Dolphyn_to_Macro/Dolphyn vs. Macro/Python Codes/`, and the analysis scripts here import from there.

Both plot scripts take the same arguments:
```
python3 c_lf_lcoe_by_fuel_plot.py   [case_dir ...] [--out DIR] [--no-dmcc]
python3 c_ethylene_lcoe_plot.py     [case_dir ...] [--out DIR] [--no-dmcc]
```
With no case_dir, they run the baseline ethylene matrix (`baseline/<M>/1c_<M>_CCfermflue_blend_jet_diesel_gasoline_ethylene`) into `baseline/plots_1c_CCfermflue_blend_jet_diesel_gasoline_ethylene`. `case_dir` is the folder holding `assets/`. Each figure is written as png and pdf, plus `_rows.csv` (one row per zone/feedstock) and `_bars.csv` (the plotted bars).

### Plots generated (all under `macro/10_31_SCENARIO_26w/`)
| Folder | Cases | Plots |
|---|---|---|
| `baseline/plots_1c_CCfermflue_blend_jet_diesel_gasoline_ethylene/` | 1c_{HB_HS,HB_LS,LB_HS,LB_LS}_…_ethylene | liquid fuels + ethylene |
| `baseline/plots_1c_CCfermflue_blend_jet_diesel_gasoline_ethylene_nosequestration/` | …_ethylene_nosequestration (4) | liquid fuels + ethylene |
| `no_corn/plots_1_CCfermflue_blend_jet_diesel_gasoline_ethylene_no_corn/` | 1_{M}_…_ethylene_no_corn (4) | liquid fuels + ethylene, no DM-CC |
| `baseline/HB_HS/plots_1c_HB_HS_CCfermflue/` | 1c_HB_HS_CCfermflue_blend_jet_diesel_gasoline | liquid fuels |
| `baseline/HB_HS/1c_HB_HS_CCfermflue_blend_jet/` | jet-only ethanol upgrade case | liquid fuels |
| `sensitivity_lfcost/plots_1_CCfermflue_blend_jet_diesel_gasoline/` | fossil diesel/jet price swap (HB_HS) | liquid fuels |

The corn_price and fixed_om sweeps were analysed with `sweep_levers.py` but have no LCOE plots yet.

## 2. LCOE method (Python port of the Excel templates)

- **Cost components.** Each asset row costs, per unit of product:
  - capital = investment_cost / output / (0.9·8760)
  - fixed O&M = fixed_om_cost / output / (0.9·8760)
  - variable O&M = variable_om_cost / output
  - inputs = consumption / output × zone dual
  - CO₂ capture = −(co2_sink + co2_captured dual) × captured / output
  - CO₂ emissions = co2_sink × (end-use C + process emissions + captured − biogenic uptake) / output

  The capture/emissions split is the templates' "method 1". End-use emission rates are read from each case's `*_end_use.json`, so sequestration vs no-sequestration is handled automatically.
- **Duals.** Hours-weighted with `time_weights.csv`: Σ dualₜ·wₜ / Σ wₜ. A zone missing a biomass node (e.g. no herbaceous biomass in CA) uses the average over zones that have it; a note is printed.
- **Liquid fuels.** Cost is per MWh of **total** fuel output; co-products are not credited.
- **Ethylene.** Cost is in $/t, plotted in $/GJ (×1/50.3). H₂, natural gas and gasoline co-products are credited at their duals. Synthetic MS+MTO variable O&M is per t-ethylene, as in the template; this choice is validated against model behaviour. Existing crackers carry no capex; retrofits carry retrofit capex only.
- **Zones and feedstocks → one bar per technology category (per fuel panel).**
  - Deployed: weighted average, using each row's **annual** fuel-specific production (Σ flowₜ·wₜ) as the weight.
  - Not deployed: the single cheapest row.
- **Ethanol feedstock versions.** Every ethanol route (E-Blend, E-G, E-GD, E-D, E-J, and Dehydration H2fuel / NGfuel) is shown up to three times:
  - **(DM-CC)**: reconstructed existing dry mill with CC on fermentation + flue gas. No new-build capex. Capex = only the CC retrofit (45,179 from `existing_drymill.json` retrofit_options). Full post-retrofit fixed O&M (201,481). Dropped automatically if the case has no dry mill, or with `--no-dmcc`.
  - **(BC-X)**: reconstructed biochemical `Bio_Ethanol_X`, no CC, where X is the feedstock (Agri/Herb/Wood) with the most ethanol production in that case.
  - **(dual)**: the `ethanol_global` shadow price, i.e. the opportunity cost of ethanol.

  Reconstructed producers are costed at the consuming asset's zone duals, as in the template. Blending has no zone, so its reconstructed rows are weighted by where ethanol is produced. Reconstructed production costs are drawn hatched.
- **Checkmarks.**
  - Route deployed: production above 0.0001 EJ = 27,778 MWh for liquid fuels; above 0.01% of demand = 5,000 t for ethylene.
  - **And**, for DM-CC/BC bars, that ethanol pathway also produced above 27,778 MWh.

  Macro pools ethanol at one node, so this can't trace which producer fed which upgrader.
- **Validation.** The marginal deployed route's LCOE lands within ~1–2% of its demand dual in every case. Examples: bio-ethylene (dual) vs the ethylene dual, both with and without sequestration; B-G and B-J-CC84 vs the gasoline/jet duals.

## 3. Netback (how to read the economics)

> netback ($/MWh ethanol) = yield × (product demand dual − route's non-ethanol cost per unit product)

This is the most a route can pay for ethanol and still break even.
- Ethanol goes to the highest-netback uses first.
- The ethanol dual equals the netback of the **marginal** use.
- Inframarginal uses earn a rent (netback − dual) equal to the shadow price of whatever caps them (e.g. the 7.1% blend limit).
- Comparing netbacks to the producers' reconstructed costs shows the scarcity rent.
- The gap (dual − netback) gives break-even targets, e.g. jet needs about +68 $/MWh-jet.

Caveats: duals are marginal; use the product node the route actually sells into; the 0.9 capacity factor understates the diesel netback by about 5 $/MWh.

## 4. Findings: where ethanol goes and why

Netbacks in $/MWh ethanol. Typical values: blend 62–72, ethylene 35–51 (≈ ethanol dual, i.e. marginal), diesel 30–39, **jet −9 to −28 (never pays)**.

| Case group | Ethanol dual | Produced / blend / diesel / ethylene / jet (TWh) |
|---|---|---|
| Blend + jet only (HB_HS) | 32 | 115 / 115 / – / – / 0; **67% of dry mill retires** |
| Blend + all LF (HB_HS) | 42 | 365 / 115 / 250 / – / 0 |
| LF-cost sensitivity (HB_HS) | 36 | 381 / 115 / 266 / – / 0 |
| + ethylene, sequestration (4 cases) | 36–43 | 351–446 / 107–115 / 0–157 / 174–243 / 0 |
| + ethylene, no sequestration (4) | 37–44 | 351–403 / 104–115 / 3–114 / 174–240 / 0 |
| + ethylene, no corn HB (2) | 48–52 | 261–289 / 109–115 / 0 / 146–180 / 0 |
| + ethylene, no corn LB (2) | 150–163 | **0 ethanol made** |

### Levers
1. **Blend cap vs cheap supply.** Existing dry mills (sunk capex, cheap CC retrofit) can make about 350 TWh; blending takes about 115 TWh. The surplus needs an outlet. With no profitable outlet (jet only), the dry mills retire.
2. **Product value net of upgrade cost.** Diesel is worth ~30–40 $/MWh more than jet. Jet upgrading also costs more (capex 331k vs 247k, FOM 181k vs 135k, more H₂), so jet's netback is negative even with free ethanol. The diesel and jet duals are set by competing bio routes and refinery ratios, not by fossil prices: swapping fossil prices only lowered the ethanol dual.
3. **Ethylene vs diesel.** Ethylene is the marginal outlet (its netback ≈ the ethanol dual) and takes ~145–245 TWh (~10–17 Mt of 50 Mt). Diesel gets the residual, so it's larger when extra cheap biochemical ethanol exists (HB_HS) and zero in LB_LS.
4. **Ethanol supply cost (corn, biomass).** With corn the ethanol dual is stable (36–43) across the matrix. Without corn, HB makes biochemical ethanol at a higher dual; in LB, residue at 400+ $/t makes ethanol cost more than any use can pay.
5. **Sequestration** raises the ethylene dual 2–3× (635–700 → 1,150–2,030 $/t) but barely changes the allocation. Bio-ethylene's advantage over fossil (≈3.14 t-CO₂/t × CO₂ price) is the same either way.

### Sensitivity sweeps (`sweep_*.csv`)
- **Corn price** (levels 10/25/50/75/90 = 134/143/160/204/247 $/t; 50 = baseline).
  - Nothing changes until dry-mill cost approaches the ethanol dual; below that, dry-mill ethanol earns a rent.
  - **HB_HS:** retirement starts between 160 and 204 $/t (80% retired at 204, 99% at 247). Diesel loses first (157 → 8 → 0 TWh); ethylene keeps ~150–175 TWh by switching to biochemical ethanol.
  - At 247 $/t, HB_HS ≈ the no-corn case (ethanol dual 51.6 vs 51.7; ethylene dual 835 vs 835).
  - **HB_LS** retires only at 247 $/t (75%).
  - **LB** never retires: CO₂ at 325–405 $/t makes dry-mill cost negative. My rough estimate is that corn would need to exceed ~400 $/t.
  - Dry-mill cost rises about 0.26 $/MWh-ethanol per $/t corn. My reconstruction is still ~7 $/MWh below the dual at retirement (0.9 CF / average-dual simplifications), so treat the threshold as a band.
- **Dry-mill fixed O&M** (100/115/130/145% of baseline; existing 176,728 → 256,256, retrofit 201,481 → 281,009).
  - **No change in any case.** +15% ≈ +1.1 $/MWh-ethanol ≈ +4 $/t corn.
  - To tip retirement, O&M would need to rise roughly 2.5× (HB_HS) to 4× (HB_LS); in LB it would never be enough.

**Bottom line:** ethanol goes beyond blending only when cheap ethanol (mainly existing corn dry mills) exceeds the blend cap and an outlet's product is valuable enough: ethylene first, diesel second, jet never. Dry-mill ethanol has a cushion of about 15–30 $/MWh (HB) and >70 $/MWh (LB) below the marginal use's netback. Cost sensitivities only matter once they exhaust it: corn price can in HB; dry-mill O&M can't.

## 5. Bugs fixed / gotchas
- The ethylene component list originally lacked "Biomass", so reconstructed feedstock cost was silently dropped. Fixed; a missing component now raises an error.
- Synthetic ethylene variable O&M must be per t-ethylene (dividing by yield made MS+MTO falsely undercut the dual).
- zsh doesn't word-split `$VAR` lists; pass case paths explicitly.
- The first HB_HS plot used a producer-mix ethanol cost (superseded); every folder above has been regenerated with the current method.

## 6. Possible next steps
- Ethanol allocation and dry-mill retirement vs corn price (one panel per biomass/storage case), with the ethanol dual and DM-CC cost overlaid.
- LCOE plots for the corn_price and fixed_om sweep cases.
- Dispatch-weighted duals (weight dualₜ by the asset's own flowₜ) instead of hours-weighted, plus actual capacity factors.
- Netback columns in `_bars.csv`, or a netback-vs-ethanol-dual chart.
