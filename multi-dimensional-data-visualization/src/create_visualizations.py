"""
Script to generate multi‑dimensional data visualizations for the
CMP_SC‑8630 data visualization assignment.  The script loads three
real‑world datasets related to climate and hydrology and produces
visualizations that explore patterns across multiple variables and
dimensions.  The resulting figures are saved to the ``output``
directory.  The datasets used here include:

* ``weather_data.csv`` – daily weather observations for multiple
  cities in New Zealand (2016–2017) containing temperature,
  humidity, wind, pressure and precipitation variables.  Source:
  mosaicData package within the Rdatasets collection.
* ``global_temp.csv`` – NASA Goddard Institute for Space Studies
  (GISTEMP) global land–ocean temperature anomalies from 1880 to
  2025.  Monthly anomalies relative to the 1951–1980 baseline are
  provided.  Source: NASA GISS via data.giss.nasa.gov.
* ``minnesota_weather.csv`` – monthly weather summary for six
  Minnesota agricultural sites (1927–1936) including cooling and
  heating degree days, precipitation and temperature extremes.
  Source: agridat package within Rdatasets.

The visualizations include heatmaps, scatter plots and line charts
to illustrate how variables such as temperature, humidity and
precipitation vary over time and across different locations.
"""

from pathlib import Path
from typing import List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import seaborn as sns
import numpy as np


# Calendar month abbreviations used by several of the plots below.
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def ensure_output_dir(path: str) -> None:
    """Ensure that the output directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def plot_weather_heatmap(df: pd.DataFrame, outdir: str) -> str:
    """Create a heatmap of average temperature by city and month.

    Parameters
    ----------
    df : pandas.DataFrame
        Weather data with columns ``city``, ``month`` and ``avg_temp``.
    outdir : str
        Directory to write the output image.

    Returns
    -------
    str
        Path to the saved figure.
    """
    # 1. Average monthly temperature per city.
    monthly = df.groupby(["city", "month"], as_index=False)["avg_temp"].mean()

    # 2./3. Pivot to a city x month matrix with months in calendar order.
    matrix = monthly.pivot(index="city", columns="month", values="avg_temp")
    matrix = matrix.reindex(sorted(matrix.columns), axis=1)

    # 4. Draw the heatmap.
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(
        matrix,
        cmap="coolwarm",
        annot=True,
        fmt=".1f",
        cbar_kws={"label": "Average temperature"},
        ax=ax,
    )

    # 5. Labels.
    ax.set_title("Average monthly temperature by city")
    ax.set_xlabel("Month")
    ax.set_ylabel("City")

    # 6. Save.
    out_path = str(Path(outdir) / "weather_heatmap.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_weather_scatter(df: pd.DataFrame, outdir: str) -> str:
    """Create a scatter plot exploring relationships between humidity,
    temperature and precipitation.

    Each point represents a daily observation.  The x‑axis shows
    average humidity, the y‑axis shows average temperature in Fahrenheit,
    the marker size encodes precipitation and colour encodes the city.
    Separate legends are provided for city and precipitation to avoid
    overlap.

    Parameters
    ----------
    df : pandas.DataFrame
        Weather data with columns ``avg_humidity``, ``avg_temp``,
        ``precip`` and ``city``.
    outdir : str
        Directory to write the output image.

    Returns
    -------
    str
        Path to the saved figure.
    """
    # 1. Clean the precipitation column (e.g. "T" trace values become 0.0).
    df = df.copy()
    df["precip"] = pd.to_numeric(df["precip"], errors="coerce").fillna(0.0)

    # 2./3. Figure and marker size range.
    fig, ax = plt.subplots(figsize=(9, 6))
    size_range = (20, 300)

    # Use an explicit palette/order so the custom legend matches the markers.
    cities = sorted(df["city"].dropna().unique())
    palette = sns.color_palette(n_colors=len(cities))
    color_map = dict(zip(cities, palette))

    # 4. Scatter plot (default legend hidden; we build two custom ones).
    sns.scatterplot(
        data=df,
        x="avg_humidity",
        y="avg_temp",
        hue="city",
        hue_order=cities,
        palette=palette,
        size="precip",
        sizes=size_range,
        alpha=0.65,
        legend=False,
        ax=ax,
    )
    ax.set_xlabel("Average relative humidity (%)")
    ax.set_ylabel("Average temperature (°F)")

    # 5. Custom legend for cities (colour / hue).
    city_handles = [
        mlines.Line2D(
            [], [], marker="o", linestyle="None", markersize=8,
            markerfacecolor=color_map[c], markeredgecolor=color_map[c], label=c,
        )
        for c in cities
    ]
    city_legend = ax.legend(
        handles=city_handles,
        title="City",
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
    )
    ax.add_artist(city_legend)

    # 6. Custom legend for precipitation (marker size).
    precip_max = float(df["precip"].max())
    precip_values = np.linspace(0.0, precip_max, 4)
    precip_handles = []
    for value in precip_values:
        marker_size = float(np.interp(value, [0.0, precip_max], size_range))
        handle = ax.scatter(
            [], [], s=marker_size, color="gray", alpha=0.65,
            label=f"{value:.2f}",
        )
        precip_handles.append(handle)
    ax.legend(
        handles=precip_handles,
        title="Precipitation",
        loc="lower left",
        bbox_to_anchor=(1.02, 0.0),
    )

    # 7. Title.
    ax.set_title("Daily weather: temperature vs humidity with precipitation (size)")

    # 8. Save.
    out_path = str(Path(outdir) / "weather_scatter.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_global_temp_heatmap(df: pd.DataFrame, outdir: str) -> str:
    """Create a heatmap of global temperature anomalies by year and month.

    Parameters
    ----------
    df : pandas.DataFrame
        Global temperature anomalies where rows correspond to years and
        columns to months (Jan–Dec).  The DataFrame should include
        numeric values for anomalies.  Missing values are allowed and
        will appear as blank cells.
    outdir : str
        Directory to write the output image.

    Returns
    -------
    str
        Path to the saved figure.
    """
    # 1. Wide -> long.
    long_df = df.melt(
        id_vars="Year",
        value_vars=MONTH_ABBR,
        var_name="Month",
        value_name="Anomaly",
    )

    # 2. Map month abbreviations to chronological numbers (1-12).
    month_to_num = {abbr: i + 1 for i, abbr in enumerate(MONTH_ABBR)}
    long_df["MonthNum"] = long_df["Month"].map(month_to_num)

    # 3./4. Pivot back to a Year x Month matrix, sorted by year ascending.
    matrix = long_df.pivot(index="Year", columns="MonthNum", values="Anomaly")
    matrix = matrix.sort_index(ascending=True)

    # 5./6. Heatmap.
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        matrix,
        cmap="coolwarm",
        vmin=-1.5,
        vmax=1.5,
        cbar_kws={"label": "Temperature anomaly (°C relative to 1951–1980)"},
        linewidths=0,
        linecolor="white",
        ax=ax,
    )

    # 7. Month abbreviations on the x-axis, rotated 45°.
    ax.set_xticks(np.arange(len(MONTH_ABBR)) + 0.5)
    ax.set_xticklabels(MONTH_ABBR, rotation=45)

    # 8. Labels.
    ax.set_title("Global land–ocean temperature anomalies (1880–2025)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")

    # 9. Save.
    out_path = str(Path(outdir) / "global_temp_heatmap.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_minnesota_precip_line(df: pd.DataFrame, outdir: str) -> str:
    """Create a line chart of monthly precipitation by site over time.

    This figure shows how precipitation varies across the six Minnesota
    sites from 1927 to 1936.  Each line corresponds to a site and
    month; values are aggregated by year and month.

    Parameters
    ----------
    df : pandas.DataFrame
        Minnesota weather data with columns ``site``, ``year``, ``mo`` (month) and
        ``precip``.
    outdir : str
        Directory to write the output image.

    Returns
    -------
    str
        Path to the saved figure.
    """
    # 1. Build a datetime column from year + month (day = 1).
    df = df.copy()
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["mo"], day=1)
    )

    # 2./3. Line plot, one line per site.
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(data=df, x="date", y="precip", hue="site", ax=ax)
    ax.set_xlabel("Year")
    ax.set_ylabel("Precipitation (inches)")

    # 4. Title.
    ax.set_title("Monthly precipitation by Minnesota site (1927–1936)")

    # 5. Legend outside the plot box.
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="Site")

    # 6. Save.
    out_path = str(Path(outdir) / "minnesota_precip_line.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> List[str]:
    """Run all visualizations and return a list of generated file paths."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    out_dir = base_dir / "output"
    ensure_output_dir(str(out_dir))
    figures: List[str] = []

    # Load and plot weather data
    weather_df = pd.read_csv(data_dir / "weather_data.csv")
    # Plot heatmap and scatter
    figures.append(plot_weather_heatmap(weather_df, str(out_dir)))
    figures.append(plot_weather_scatter(weather_df, str(out_dir)))

    # Load and plot global temperature anomalies
    global_df = pd.read_csv(data_dir / "global_temp.csv", skiprows=1)
    # Replace *** with NA and convert to numeric
    global_df = global_df.replace("***", pd.NA)
    for col in global_df.columns[1:]:
        global_df[col] = pd.to_numeric(global_df[col], errors="coerce")
    figures.append(plot_global_temp_heatmap(global_df, str(out_dir)))

    # Load and plot Minnesota weather data
    minn_df = pd.read_csv(data_dir / "minnesota_weather.csv")
    figures.append(plot_minnesota_precip_line(minn_df, str(out_dir)))
    return figures


if __name__ == "__main__":
    generated = main()
    print("Generated figures:")
    for path in generated:
        print(path)