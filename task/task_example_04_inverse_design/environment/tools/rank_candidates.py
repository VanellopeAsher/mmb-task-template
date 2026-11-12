import pandas as pd
p="/workspace/data/candidate_performance.csv"
df=pd.read_csv(p)
feasible=df[(df.purity>=0.78)&(df.recovery>=0.55)&(df.working_capacity_mol_kg>=1.0)&(df.thermal_energy_MJ_mol<=0.070)&(df.enrichment_xCH4_0_003>=1.85)]
print(feasible.to_string(index=False))
