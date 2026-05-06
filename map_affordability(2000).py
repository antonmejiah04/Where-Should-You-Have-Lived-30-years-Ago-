import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Plot settings
plt.rcParams["figure.dpi"] = 300

#%%
# paths and settings
gap_csv = os.path.join("data", "wages_vs_rent_2000.csv")
shapefile = os.path.join("shapefiles", "cb_2025_us_state_500k.zip")
output_dir = "maps_2000"
target_years = [2000, 2005, 2010, 2015, 2020, 2024]

# Using a diverging colormap: Red = worse for workers (rent outpaces wages), Blue = better
cmap = "RdBu_r" 
baseline_year = 2000

# You may need to adjust vmin and vmax based on your actual data spread
vmin, vmax = -40, 40 
conus_epsg = 5070
ak_epsg = 3338
hi_epsg = 32604
ak_fips = "02"
hi_fips = "15"
valid_fips = {
    "01","02","04","05","06","08","09","10","11","12","13","15","16","17","18",
    "19","20","21","22","23","24","25","26","27","28","29","30","31","32","33",
    "34","35","36","37","38","39","40","41","42","44","45","46","47","48","49",
    "50","51","53","54","55","56"
}

#%%
# Load affordability gap csv (long format) and pivot to wide format for mapping
df_long = pd.read_csv(gap_csv, dtype={"state_fips": str})
df_long["state_fips"] = df_long["state_fips"].str.zfill(2)

# Pivot so that each year is a column (matches how map_wages works)
gap_wide = df_long.pivot(index="state_fips", columns="year", values="affordability_gap").reset_index()
gap_wide.columns.name = None

# Filter target_years to those actually present in the data
target_years = [yr for yr in target_years if yr in gap_wide.columns]

#%%
# Load shapefile, filter to valid states, merge gap data, reproject
states_raw = gpd.read_file(shapefile)
states_raw = states_raw[states_raw["STATEFP"].isin(valid_fips)].copy()
states_raw = states_raw[["STATEFP", "STUSPS", "NAME", "geometry"]]

# Merge the pivoted gap data
states = states_raw.merge(gap_wide, left_on="STATEFP", right_on="state_fips", how="left")

is_ak = states["STATEFP"] == ak_fips
is_hi = states["STATEFP"] == hi_fips
conus  = states[~is_ak & ~is_hi].copy().to_crs(epsg=conus_epsg)
alaska = states[is_ak].copy().to_crs(epsg=ak_epsg)
hawaii = states[is_hi].copy().to_crs(epsg=hi_epsg)

#%%
# Helper: draw one choropleth panel
def draw_panel(ax, gdf, col, v_min, v_max, colormap, add_legend=False, edgecolor="white", linewidth=0.4):
    has_data = gdf[col].notna()
    if has_data.any():
        gdf[has_data].plot(
            column      = col,
            cmap        = colormap,
            vmin        = v_min,
            vmax        = v_max,
            edgecolor   = edgecolor,
            linewidth   = linewidth,
            legend      = add_legend,
            legend_kwds = {"label": f"pp gap vs {baseline_year} (+ = rent outpacing wages)", "shrink": 0.65, "pad": 0.01},
            ax          = ax
        )
    ax.axis("off")

#%%
# Generate and save one map per target year
os.makedirs(output_dir, exist_ok=True)
for year in target_years:
    print(f"generating map for {year}...")
    fig, ax_main = plt.subplots(1, 1, figsize=(20, 12))
    plt.subplots_adjust(left=0.01, right=0.88, top=0.93, bottom=0.08)
    
    ax_ak = fig.add_axes([0.01, 0.02, 0.18, 0.22])
    ax_hi = fig.add_axes([0.20, 0.02, 0.10, 0.12])
    
    draw_panel(ax_main, conus,  year, vmin, vmax, cmap, add_legend=True,  linewidth=0.5)
    draw_panel(ax_ak,   alaska, year, vmin, vmax, cmap, add_legend=False, linewidth=0.4)
    draw_panel(ax_hi,   hawaii, year, vmin, vmax, cmap, add_legend=False, linewidth=0.4)
    
    conus.boundary.plot( color="black", linewidth=1, ax=ax_main)
    alaska.boundary.plot(color="black", linewidth=1, ax=ax_ak)
    hawaii.boundary.plot(color="black", linewidth=1, ax=ax_hi)

    ax_main.set_title(
        f"US State Affordability Gap — {year}\n"
        f"Percentage Points vs {baseline_year} Baseline  |  Red = Worse for Workers",
        fontsize=22, pad=10, fontweight="bold"
    )
    median_gap = conus[year].median()
    if pd.notna(median_gap):
        ax_main.annotate(
            f"median state gap: {median_gap:+.1f} pp",
            xy=(0.02, 0.97), xycoords="axes fraction",
            fontsize=12, va="top", color="dimgrey", style="italic"
        )
        
    out_path = os.path.join(output_dir, f"affordability_map_{year}.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()