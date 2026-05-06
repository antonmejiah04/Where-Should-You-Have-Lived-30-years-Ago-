import pandas as pd
import os
import zipfile

#%%
# Setting up the data location and output folder
flat_file_dir = "QCEW Data Files"
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)
all_years = range(1990, 2025)

# State FIPS Codes for all 50 states & DC
state_fips = {
    "01","02","04","05","06","08","09","10","11","12",
    "13","15","16","17","18","19","20","21","22","23",
    "24","25","26","27","28","29","30","31","32","33",
    "34","35","36","37","38","39","40","41","42","44",
    "45","46","47","48","49","50","51","53","54","55","56"
}

#%%
# Load each annual flat file, filter to state-level private wages, and store records
records = []
for year in all_years:
    zip_name = f"{year}_annual_singlefile.zip"
    csv_name = f"{year}.annual.singlefile.csv"
    fpath = os.path.join(flat_file_dir, zip_name)
    try:
        archive = zipfile.ZipFile(fpath)
        fh = archive.open(csv_name)
        raw = pd.read_csv(fh, dtype={"area_fips": str}, low_memory=False)
        raw.columns = raw.columns.str.strip()
        raw["own_code"] = pd.to_numeric(raw["own_code"], errors="coerce").fillna(0).astype(int)
        raw["industry_code"] = pd.to_numeric(raw["industry_code"], errors="coerce").fillna(0).astype(int)
    except Exception as e:
        print(f"Could not read file for {year}: {e}")
        continue

    # Filters statewide rows (area_fips = SS000), private ownership in all industries
    mask = (
        raw["area_fips"].str.endswith("000") &
        (raw["area_fips"] != "00000") &
        (raw["own_code"] == 5) &
        (raw["industry_code"] == 10)
    )
    state_data = raw[mask].copy()
    state_data["state_fips"] = state_data["area_fips"].str[:2]
    state_data["year"] = year
    state_data = state_data.rename(columns={"annual_avg_wkly_wage": "avg_weekly_wage"})

    # Keep only valid state rows & confirmation year data loads (no territories)
    state_data = state_data[state_data["state_fips"].isin(state_fips)]
    records.extend(state_data[["state_fips", "year", "avg_weekly_wage"]].to_dict("records"))

#%%
# Create DataFrame
df = pd.DataFrame(records)
df = df.drop_duplicates(subset=["state_fips", "year"])
df.sort_values(["state_fips", "year"], inplace=True)

# Creates one row per state, one column per year
wages_wide = df.pivot(
    index   = "state_fips",
    columns = "year",
    values  = "avg_weekly_wage"
)
wages_wide = wages_wide.sort_index(axis=1)

# Calculate percentage growth relative to 1990 and 2000 baselines
wages_growth = (wages_wide.div(wages_wide[1990], axis=0) - 1) * 100
wages_growth_2000 = (wages_wide.div(wages_wide[2000], axis=0) - 1) * 100

# Save output Files
wages_wide.to_csv(os.path.join(output_dir, "wages_wide.csv"))
wages_growth.to_csv(os.path.join(output_dir, "wages_growth.csv"))
wages_growth_2000.to_csv(os.path.join(output_dir, "wages_growth_2000.csv"))