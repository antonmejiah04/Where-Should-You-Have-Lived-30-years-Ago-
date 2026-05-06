import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Plot settings
plt.rcParams["figure.dpi"] = 300

#%%
# Paths and settings
combined_file = os.path.join("data", "wages_vs_rent.csv")
shapefile = os.path.join("shapefiles", "cb_2024_us_state_500k.zip")
output_dir = "maps"
target_years = [1995, 2000, 2005, 2010, 2015, 2020, 2024]
cmap = "RdBu_r"
baseline_year = 1990
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
# Load wages_vs_rent.csv and pivot affordability gap to wide form
combined = pd.read_csv(combined_file, dtype={"state_fips": str})
combined["state_fips"] = combined["state_fips"].str.zfill(2)
gap_wide = combined.pivot_table(
    index="state_fips", columns="Year", values="affordability_gap", aggfunc="mean"
).reset_index()
year_cols = [c for c in gap_wide.columns if c != "state_fips"]
gap_wide = gap_wide.rename(columns={c: int(c) for c in year_cols})
target_years = [yr for yr in target_years if yr in gap_wide.columns]

#%%
# Compute symmetric vmin/vmax so white lands exactly at 0 (parity)
gap_vals = combined["affordability_gap"].dropna()
max_abs  = max(abs(gap_vals.min()), abs(gap_vals.max()))
vmin = -round(max_abs, -1)
vmax =  round(max_abs, -1)

#%%
# load shapefile, filter to valid states, merge gap data, reproject
states_raw = gpd.read_file(shapefile)
states_raw = states_raw[states_raw["STATEFP"].isin(valid_fips)].copy()
states_raw = states_raw[["STATEFP", "STUSPS", "NAME", "geometry"]]
states = states_raw.merge(gap_wide, left_on="STATEFP", right_on="state_fips", how="left")
is_ak = states["STATEFP"] == ak_fips
is_hi = states["STATEFP"] == hi_fips
conus = states[~is_ak & ~is_hi].copy().to_crs(epsg=conus_epsg)
alaska = states[is_ak].copy().to_crs(epsg=ak_epsg)
hawaii = states[is_hi].copy().to_crs(epsg=hi_epsg)

#%%
# Draw one choropleth panel
def draw_panel(ax, gdf, col, v_min, v_max, colormap, add_legend=False, edgecolor="white", linewidth=0.4):
    has_data = gdf[col].notna()
    if has_data.any():
        gdf[has_data].plot(
            column = col,
            cmap = colormap,
            vmin = v_min,
            vmax = v_max,
            edgecolor = edgecolor,
            linewidth = linewidth,
            legend = add_legend,
            legend_kwds = {
                "label":  f"Rent Growth - Wage Growth (pp vs. {baseline_year})\nRed = Rent Outpacing Wages  |  Blue = Wages Ahead",
                "shrink": 0.65,
                "pad":    0.01
            },
            ax = ax
        )
    ax.axis("off")
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
        f"Rent Growth vs. Wage Growth (% Change from {baseline_year} Baseline)",
        fontsize=22, pad=10, fontweight="bold"
    )
    median_gap = conus[year].median()
    if pd.notna(median_gap):
        ax_main.annotate(
            f"Median State Gap: {median_gap:+.1f} pp",
            xy=(0.02, 0.97), xycoords="axes fraction",
            fontsize=12, va="top", color="dimgrey", style="italic"
        )
    out_path = os.path.join(output_dir, f"affordability_gap_{year}.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()