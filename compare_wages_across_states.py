import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Plot settings
plt.rcParams["figure.dpi"] = 300
sns.set_theme(style="white")

#%%
# Paths and settings
growth_csv   = os.path.join("data", "wages_growth.csv")
charts_dir   = "charts"
baseline_year = 1990
target_years  = [1995, 2000, 2005, 2010, 2015, 2020, 2024]

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
# Helps save a figure
def save_chart(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.show()
    print(f"saved - {os.path.abspath(path)}")

#%%
# Load wage growth csv and rename year columns to integers
wages_growth = pd.read_csv(growth_csv, dtype={"state_fips": str})
wages_growth["state_fips"] = wages_growth["state_fips"].str.zfill(2)
year_cols = [c for c in wages_growth.columns if c != "state_fips"]
wages_growth = wages_growth.rename(columns={c: int(c) for c in year_cols})

# Melt to long form (used by scatter only)
long_form = wages_growth.melt(id_vars="state_fips", var_name="Year", value_name="growth_pct")
long_form["Year"] = long_form["Year"].astype(int)

# Filter target_years to those actually present in the data
target_years = [yr for yr in target_years if yr in wages_growth.columns]

#%%
# Scatter plot and computes yearly median and 25th/75th percentiles across all states
yearly_median = long_form.groupby("Year")["growth_pct"].median()
yearly_p25    = long_form.groupby("Year")["growth_pct"].quantile(0.25)
yearly_p75    = long_form.groupby("Year")["growth_pct"].quantile(0.75)
fig, ax = plt.subplots(figsize=(14, 8))
long_form.plot.scatter(ax=ax, x="Year", y="growth_pct",
    color="steelblue", alpha=0.3, s=18, zorder=2)
ax.plot(yearly_median.index, yearly_median.values,
    color="darkred", linewidth=2.5, label="median", zorder=4)
ax.fill_between(yearly_p25.index, yearly_p25.values, yearly_p75.values,
    alpha=0.15, color="steelblue", label="25th-75th percentile", zorder=1)
ax.axhline(0, color="black", linewidth=0.8, linestyle="--", zorder=3)
ax.set_xlabel("Year")
ax.set_ylabel(f"% Change from {baseline_year} Baseline")
ax.set_title(
    f"US State Average Weekly Wage Growth vs. {baseline_year} Baseline\n"
    "Each Point = One State | Red Line = National Median",
    fontsize=14, fontweight="bold"
)
ax.set_xlim(left=long_form["Year"].min() - 0.5)
ax.legend()
save_chart(fig, os.path.join(charts_dir, "wage_growth_scatter.png"))

#%%
# Rankings heatmap and builds rankings dataframe sorted by average growth, map fips to full state names
rankings = wages_growth[["state_fips"] + target_years].copy()
rankings["state"]          = rankings["state_fips"].map(lambda x: fips_info.get(x, ("unknown", "??"))[0])
rankings["avg_growth_pct"] = rankings[target_years].mean(axis=1)
rankings = rankings.sort_values("avg_growth_pct", ascending=False).reset_index(drop=True)
heat_data = rankings.set_index("state")[target_years]

fig2, ax2 = plt.subplots(figsize=(14, 18))
sns.heatmap(
    heat_data,
    annot      = True,
    fmt        = ".1f",
    cmap       = "RdYlGn",
    linewidths = 0.4,
    linecolor  = "white",
    vmin       = 0,
    vmax       = 350,
    cbar_kws   = {"label": f"% change from {baseline_year} baseline", "shrink": 0.5},
    ax         = ax2
)
ax2.set_title(
    "US State Average Weekly Wage Growth by Year\n"
    "Ranked Best to Worst by Average Growth Across Selected Years",
    fontsize=14, fontweight="bold", pad=14
)
ax2.set_xlabel("Year")
ax2.set_ylabel(None)
save_chart(fig2, os.path.join(charts_dir, "state_rankings_heatmap.png"))
