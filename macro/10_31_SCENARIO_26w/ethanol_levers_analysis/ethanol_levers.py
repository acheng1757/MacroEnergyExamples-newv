"""Ethanol allocation, duals and netbacks across the main scenario cases (writes ethanol_levers_cases.csv)."""
import sys, os, io, contextlib
import pandas as pd
L = "/Users/abbie/Desktop/Dolphyn_to_Macro/Dolphyn vs. Macro/Python Codes/lcoe"
sys.path.insert(0, f"{L}/liquid_fuels"); sys.path.insert(0, f"{L}/ethylene")
import c_lf_lcoe_by_fuel_plot as lf
import c_ethylene_lcoe_plot as eth
S = "/Users/abbie/MacroEnergyExamples.jl/macro/10_31_SCENARIO_26w"
M = ["HB_HS", "HB_LS", "LB_HS", "LB_LS"]
cases = [("base: blend+jet only", "HB_HS", f"{S}/baseline/HB_HS/1c_HB_HS_CCfermflue_blend_jet"),
         ("base: blend+all LF", "HB_HS", f"{S}/baseline/HB_HS/1c_HB_HS_CCfermflue_blend_jet_diesel_gasoline"),
         ("lfcost sens: all LF", "HB_HS", f"{S}/sensitivity_lfcost/HB_HS/1_HB_HS_CCfermflue_blend_jet_diesel_gasoline")]
cases += [("+ethylene (seq)", m, f"{S}/baseline/{m}/1c_{m}_CCfermflue_blend_jet_diesel_gasoline_ethylene") for m in M]
cases += [("+ethylene no-seq", m, f"{S}/baseline/{m}/1c_{m}_CCfermflue_blend_jet_diesel_gasoline_ethylene_nosequestration") for m in M]
cases += [("+ethylene no corn", m, f"{S}/no_corn/{m}/1_{m}_CCfermflue_blend_jet_diesel_gasoline_ethylene_no_corn") for m in M]

def flows_sum(f, pred): return sum(abs(v) for e, v in f.items() if pred(e))
rows = []
for grp, m, d in cases:
    with contextlib.redirect_stdout(io.StringIO()):
        c = lf.Case.load(m, d)
        _, lfb = lf.lf_bars(c)
        ethb = None
        if c.has_json("ethanol_dehydration.json"):
            _, ethb = eth.ethylene_bars(c)
    f = c.flows; du = c.duals
    prod = flows_sum(f, lambda e: e.endswith("_ethanol_production_edge"))
    dm = flows_sum(f, lambda e: e.endswith("_ethanol_production_edge") and "DryMill" in e)
    blend = abs(f.get("Global_Gasoline_Blending_ethanol_edge", 0))
    up = {r: flows_sum(f, lambda e, r=r: f"_Ethanol_to_{r}_ethanol_consumption_edge" in e) for r in ("Gasoline", "Diesel", "JetFuel", "Gasoline_Diesel")}
    dehyd = flows_sum(f, lambda e: ("_B-H2in_ethanol" in e or "_B-NGin_ethanol" in e) and e.endswith("consumption_edge"))
    cap = pd.read_csv(os.path.join(d, os.path.basename(d), "results", "capacity.csv"))
    ex = cap[cap.component_id.str.contains("DryMill_Existing")]
    # netback ($/MWh ethanol) = (product dual - non-ethanol route cost) * product per MWh ethanol, using (dual) bars
    def nb_lf(cat, fuel, yield_):
        r = lfb[(lfb.category == cat) & (lfb.fuel == fuel)]
        if r.empty: return None
        r = r.iloc[0]; nonetoh = r.total - r.ethanol
        return (du[f"{fuel}_demand_global"] - nonetoh) * yield_
    nb = {"blend": nb_lf("E-Blend (dual)", "gasoline", 1.0),
          "diesel": nb_lf("E-D (dual)", "diesel", 0.950466389),
          "jet": nb_lf("E-J (dual)", "jetfuel", 0.946932606)}
    if ethb is not None:
        r = ethb[ethb.category == "Dehydration H2fuel (dual)"].iloc[0]
        nb["ethylene"] = (du["ethylene_demand_global"] - (r.total - r.ethanol)) * 0.07045276705874294
    rows.append(dict(group=grp, case=m, CO2=round(c.co2_sink), EtOH_dual=round(du["ethanol_global"], 1),
        prod_TWh=round(prod/1e6), dm_share=f"{dm/prod:.0%}" if prod else "-",
        blend=round(blend/1e6), to_diesel=round(up["Diesel"]/1e6), to_jet=round(up["JetFuel"]/1e6, 2),
        to_gas=round((up["Gasoline"]+up["Gasoline_Diesel"])/1e6, 2), to_ethylene=round(dehyd/1e6),
        dm_retired=f"{ex.retired_capacity.sum()/ex.existing_capacity.sum():.0%}" if len(ex) and ex.existing_capacity.sum() else "-",
        **{f"nb_{k}": (round(v) if v is not None else None) for k, v in nb.items()},
        eth_dual=round(du.get("ethylene_demand_global", float("nan"))), jet_dual=round(du["jetfuel_demand_global"],1),
        dsl_dual=round(du["diesel_demand_global"],1)))
df = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print("Ethanol flows in TWh (MWh/1e6); netbacks nb_* in $/MWh-ethanol; duals in $/MWh (ethylene $/t)")
print(df.to_string(index=False))
df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ethanol_levers_cases.csv"), index=False)
