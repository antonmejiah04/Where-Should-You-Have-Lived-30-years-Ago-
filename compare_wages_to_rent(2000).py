import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Plot settings
plt.rcParams["figure.dpi"] = 300
sns.set_theme(style="white")

#%%
# Paths and settings
data_dir = "data"
charts_dir = "charts_2000"
os.makedirs(data_dir, exist_ok=True)
os.makedirs(charts_dir, exist_ok=True)
wages_growth_file = os.path.join(data_dir, "wages_growth_2000.csv")
rent_growth_file  = os.path.join(data_dir, "rent_growth_2000.csv")
fips_info = {
    "01": ("Alabama",              "al"), "02": ("Alaska",         "ak"),
    "04": ("Arizona",              "az"), "05": ("Arkansas",       "ar"),
    "06": ("California",           "ca"), "08": ("Colorado",       "co"),
    "09": ("Connecticut",          "ct"), "10": ("Delaware",       "de"),
    "11": ("District of Columbia", "dc"), "12": ("Florida",        "fl"),
    "13": ("Georgia",              "ga"), "15": ("Hawaii",         "hi"),
    "16": ("Idaho",                "id"), "17": ("Illinois",       "il"),
    "18": ("Indiana",              "in"), "19": ("Iowa",           "ia"),
    "20": ("Kansas",               "ks"), "21": ("Kentucky",       "ky"),
    "22": ("Louisiana",            "la"), "23": ("Maine",          "me"),
    "24": ("Maryland",             "md"), "25": ("Massachusetts",  "ma"),
    "26": ("Michigan",             "mi"), "27": ("Minnesota",      "mn"),
    "28": ("Mississippi",          "ms"), "29": ("Missouri",       "mo"),
    "30": ("Montana",              "mt"), "31": ("Nebraska",       "ne"),
    "32": ("Nevada",               "nv"), "33": ("New Hampshire",  "nh"),
    "34": ("New jersey",           "nj"), "35": ("New Mexico",     "nm"),
    "36": ("New York",             "ny"), "37": ("North Carolina", "nc"),
    "38": ("North Dakota",         "nd"), "39": ("Ohio",           "oh"),
    "40": ("Oklahoma",             "ok"), "41": ("Oregon",         "or"),
    "42": ("Pennsylvania",         "pa"), "44": ("Rhode Island",   "ri"),
    "45": ("South Carolina",       "sc"), "46": ("South Dakota",   "sd"),
    "47": ("Tennessee",            "tn"), "48": ("Texas",          "tx"),
    "49": ("Utah",                 "ut"), "50": ("Vermont",        "vt"),
    "51": ("Virginia",             "va"), "53": ("Washington",     "wa"),
    "54": ("West Vrginia",        "wv"), "55": ("Wisconsin",       "wi"),
    "56": ("Wyoming",              "wy"),
}

#%%
# Load a growth csv and melt to long form
def load_growth_csv(filepath, value_col):
    wide = pd.read_csv(filepath, index_col=0)
    wide.index = wide.index.astype(str).str.zfill(2)
    long = (
        wide.reset_index()
        .rename(columns={"index": "state_fips"})
        .melt(id_vars="state_fips", var_name="year", value_name=value_col)
    )
    long["year"]       = pd.to_numeric(long["year"],       errors="coerce")
    long["state_fips"] = long["state_fips"].astype(str).str.zfill(2)
    return (
        long.dropna(subset=["year", value_col])
            .drop_duplicates(subset=["state_fips", "year"])
    )

# Helps save figures
def save_chart(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.show()
    print(f"saved - {os.path.abspath(path)}")

#%%
# Load both growth csvs and melt to long form
wages_long = load_growth_csv(wages_growth_file, "wage_growth")
rent_long  = load_growth_csv(rent_growth_file,  "rent_growth")

#%%
# Merge and compute affordability gap (positive = rent outpacing wages)
combined = wages_long.merge(rent_long, on=["state_fips", "year"], how="inner")
combined["affordability_gap"] = combined["rent_growth"] - combined["wage_growth"]
combined.sort_values(["state_fips", "year"], inplace=True)
combined.to_csv(os.path.join(data_dir, "wages_vs_rent_2000.csv"), index=False)

#%%
# Build heatmap data: pivot gap to wide, map fips to state names, sort worst to best
target_years = [yr for yr in [2000, 2005, 2010, 2015, 2020, 2024] if yr in combined["year"].values]
heat_df   = combined[combined["year"].isin(target_years)].drop_duplicates(subset=["state_fips", "year"])
heat_data = heat_df.pivot_table(
    index="state_fips", columns="year", values="affordability_gap", aggfunc="mean"
)
heat_data.index  = heat_data.index.map(lambda x: fips_info.get(x, ("unknown", "??"))[0])
heat_data["avg_gap"] = heat_data.mean(axis=1)
heat_data = heat_data.sort_values("avg_gap", ascending=False).drop(columns="avg_gap")

#%%
# Draw and save heatmap
fig, ax = plt.subplots(figsize=(14, 18))
sns.heatmap(
    heat_data,
    annot      = True,
    fmt        = ".1f",
    cmap       = "RdBu_r",
    center     = 0,
    linewidths = 0.4,
    linecolor  = "white",
    cbar_kws   = {"label": "pp gap: + = rent outpacing wages  |  red = worse off for workers", "shrink": 0.5},
    ax         = ax
)
ax.set_title(
    "US State Affordability Gap by Year (2000 baseline)\n"
    "Red = Rent Outpacing Wages  |  Blue = Wages Keeping Ahead of Rent",
    fontsize=14, fontweight="bold", pad=14
)
ax.set_xlabel("year")
ax.set_ylabel(None)
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)
save_chart(fig, os.path.join(charts_dir, "affordability_gap_heatmap.png"))

#%%
# Draw and save national average trend line
national_avg = combined.groupby("year")["affordability_gap"].mean().reset_index()
fig2, ax2 = plt.subplots(figsize=(12, 5))
ax2.plot(national_avg["year"], national_avg["affordability_gap"],
         color="firebrick", linewidth=2, marker="o", markersize=4)
ax2.axhline(0, color="steelblue", linewidth=1.5, linestyle="--",
            label="parity — wages keeping pace with rent")
ax2.set_title(
    "National Average Affordability Gap Over Time (2000 baseline)\n"
    "Above Zero = Rent Outpacing Wages  |  Below Zero = Wages Outpacing Rent",
    fontsize=14, fontweight="bold", pad=14
)
ax2.set_xlabel("year")
ax2.set_ylabel("Gap (Percentage Points vs. Baseline)")
ax2.legend(fontsize=10)

# Makes sure to not plot years prior to the baseline
ax2.set_xlim(left=2000)
save_chart(fig2, os.path.join(charts_dir, "affordability_gap_trend.png"))