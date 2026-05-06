import pandas as pd
import os

#%%
# Paths and settings
hud_file = os.path.join("HUD Rent Data", "FMR_2Bed_1983_2026.xlsx")
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

state_fips = {
    1,2,4,5,6,8,9,10,11,12,13,15,16,17,18,19,20,21,22,23,
    24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,
    42,44,45,46,47,48,49,50,51,53,54,55,56
}

# Read the excel file and filter to valid 50-state + dc rows only
raw = pd.read_excel(hud_file)
raw = raw[raw["state"].isin(state_fips)].copy()


# Detect all 2-bedroom fmr columns and map to calendar years
year_col_map = {}
for col in raw.columns:
    col_str = str(col)
    if col_str.startswith("fmr") and col_str.endswith("_2"):
        suffix = col_str[3:-2]
        if suffix.isdigit() and len(suffix) == 2:
            yy = int(suffix)
            year = 1900 + yy if yy >= 83 else 2000 + yy
            year_col_map[year] = col

# Aggregate to state level: median 2br fmr across all counties per state, per year
records = []
for year, col in sorted(year_col_map.items()):
    state_medians = (
        raw[["state", col]]
        .dropna(subset=[col])
        .groupby("state")[col]
        .median()
        .reset_index()
    )
    state_medians.columns = ["state_fips", "median_2br_fmr"]
    state_medians["year"] = year
    records.append(state_medians)
    
# Stack all years into one long dataframe
df = pd.concat(records, ignore_index=True)
df["state_fips"] = df["state_fips"].apply(lambda x: str(int(x)).zfill(2))
df = df.drop_duplicates(subset=["state_fips", "year"])
df.sort_values(["state_fips", "year"], inplace=True)

# Pivot to wide format: one row per state, one column per year
rent_wide = df.pivot(
    index   = "state_fips",
    columns = "year",
    values  = "median_2br_fmr"
)
rent_wide = rent_wide.sort_index(axis=1)

#%%
# Calculate percentage growth relative to 1990 and 2000 baselines
rent_growth = (rent_wide.div(rent_wide[1990], axis=0) - 1) * 100
rent_growth_2000 = (rent_wide.div(rent_wide[2000], axis=0) - 1) * 100

# Save output files
rent_wide.to_csv(os.path.join(output_dir, "rent_wide.csv"))
rent_growth.to_csv(os.path.join(output_dir, "rent_growth.csv"))
rent_growth_2000.to_csv(os.path.join(output_dir, "rent_growth_2000.csv"))