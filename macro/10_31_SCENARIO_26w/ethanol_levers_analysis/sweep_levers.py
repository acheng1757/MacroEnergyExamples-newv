"""Ethanol lever metrics across a sensitivity sweep. Usage: python3 sweep_levers.py corn_price|fixed_om"""
import sys, os, io, contextlib
import pandas as pd
L = "/Users/abbie/Desktop/Dolphyn_to_Macro/Dolphyn vs. Macro/Python Codes/lcoe"
sys.path.insert(0, f"{L}/liquid_fuels"); sys.path.insert(0, f"{L}/ethylene")
import c_lf_lcoe_by_fuel_plot as lf
import c_ethylene_lcoe_plot as eth
S = "/Users/abbie/MacroEnergyExamples.jl/macro/10_31_SCENARIO_26w"
M = ["HB_HS", "HB_LS", "LB_HS", "LB_LS"]
X = "_{m}_CCfermflue_blend_jet_diesel_gasoline_ethylene"
sweep = sys.argv[1]
levels = [10, 25, 50, 75, 90] if sweep == "corn_price" else [100, 115, 130, 145]

def fsum(f, pred): return sum(abs(v) for e, v in f.items() if pred(e))
rows = []
for m in M:
    for lvl in levels:
        d = f"{S}/{sweep}/{m}/{lvl}" + X.format(m=m)
        with contextlib.redirect_stdout(io.StringIO()):
            c = lf.Case.load(m, d)
            _, lfb = lf.lf_bars(c)
            _, ethb = eth.ethylene_bars(c)
        f, du = c.flows, c.duals
        txt = open(f"{d}/system/nodes.json").read()
        # corn price: first "price" after a biocorn node id
        i = txt.find('"biocorn_'); corn = float(txt[txt.find('"price"', i) + 8: txt.find(',', txt.find('"price"', i))]) if i >= 0 else None
        fom = next(lf.iter_instances(c.json("existing_drymill.json")))["edges"]["biomass_consumption_edge"]["fixed_om_cost"]
        prod = fsum(f, lambda e: e.endswith("_ethanol_production_edge"))
        dm = fsum(f, lambda e: e.endswith("_ethanol_production_edge") and "DryMill" in e)
        blend = abs(f.get("Global_Gasoline_Blending_ethanol_edge", 0))
        dsl = fsum(f, lambda e: "_Ethanol_to_Diesel_ethanol_consumption_edge" in e)
        jet = fsum(f, lambda e: "_Ethanol_to_JetFuel_ethanol_consumption_edge" in e)
        ethy = fsum(f, lambda e: ("_B-H2in_ethanol" in e or "_B-NGin_ethanol" in e) and e.endswith("consumption_edge"))
        cap = pd.read_csv(os.path.join(d, os.path.basename(d), "results", "capacity.csv"))
        ex = cap[cap.component_id.str.contains("DryMill_Existing")]
        excap = ex.existing_capacity.sum()
        p = lf.producer_cost(c, "DM-CC", "NCEN")
        dm_lcoe = sum(p[k] for k in lf.ETOH_KEYS) + c.co2_sink * p["upstream_c"]
        def nb_lf(cat, fuel, y):
            r = lfb[(lfb.category == cat) & (lfb.fuel == fuel)]
            if r.empty: return float("nan")
            r = r.iloc[0]; return (du[f"{fuel}_demand_global"] - (r.total - r.ethanol)) * y
        r = ethb[ethb.category == "Dehydration H2fuel (dual)"].iloc[0]
        rows.append(dict(case=m, lvl=lvl, corn=corn, dm_fom=round(fom), CO2=round(c.co2_sink),
            EtOH_dual=round(du["ethanol_global"], 1), DMCC_lcoe=round(dm_lcoe, 1),
            prod=round(prod/1e6), dm_sh=f"{dm/prod:.0%}" if prod else "-",
            blend=round(blend/1e6), diesel=round(dsl/1e6), jet=round(jet/1e6, 2), ethylene=round(ethy/1e6),
            retired=f"{ex.retired_capacity.sum()/excap:.0%}", retrofit=f"{ex.retrofitted_capacity.sum()/excap:.0%}",
            nb_blend=round(nb_lf("E-Blend (dual)", "gasoline", 1.0)), nb_dsl=round(nb_lf("E-D (dual)", "diesel", 0.950466389)),
            nb_jet=round(nb_lf("E-J (dual)", "jetfuel", 0.946932606)),
            nb_eth=round((du["ethylene_demand_global"] - (r.total - r.ethanol)) * 0.07045276705874294),
            eth_dual=round(du["ethylene_demand_global"])))
        print(f"done {m} {lvl}", file=sys.stderr)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"sweep_{sweep}.csv"), index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
print(df.to_string(index=False))
