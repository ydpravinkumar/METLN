
import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import time

st.set_page_config(page_title="Subscription Dashboard", layout="wide")
st.title("📊 Subscription Analytics Dashboard")

# ----------------------------
# File Upload Section
# ----------------------------
uploaded_files = st.file_uploader(
    "Upload one or more files (CSV or Excel)",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

# ----------------------------
# Data Loading
# ----------------------------
def load_data(files):
    dfs = []
    for file in files:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df.columns = df.columns.str.strip()

        if "Legacy Acct ID" not in df.columns:
            df["Legacy Acct ID"] = pd.NA

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


if uploaded_files:
    data = load_data(uploaded_files)

    # Convert dates
    for col in ["LastStartDate", "OriginalStartDate"]:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors="coerce")

    # Classification logic
    def classifySubscription(row):
        billMethod = str(row.get("Bill Method", "")).upper()
        rateCode = str(row.get("Rate Code", "")).upper()

        if "DIGITAL" in billMethod or "D" in rateCode:
            return "Digital"
        elif "PRINT" in billMethod or "P" in rateCode:
            return "Print"
        elif "BUNDLE" in billMethod or "B" in rateCode:
            return "Bundle"
        else:
            return "Other"

    data["SubType"] = data.apply(classifySubscription, axis=1)
    data["City"] = data["City"].astype(str).str.strip().str.title()

    # Sidebar Filters
    st.sidebar.header("Filters")
    status_filter = st.sidebar.multiselect(
        "Select Status",
        options=data["Status"].str.upper().unique(),
        default=["ACTIVE"]
    )

    # Filter data
    current = data[data["Status"].str.upper().isin(status_filter)].copy()

    # ----------------------------
    # Geocoder with Cache
    # ----------------------------
    geolocator = Nominatim(user_agent="maine_map")

    @st.cache_data
    def get_coordinates(city):
        """Geocode a city with caching + delay to avoid rate limit."""
        try:
            time.sleep(1)  # prevent API rate limit
            loc = geolocator.geocode(f"{city}, Maine")
            if loc:
                return loc.latitude, loc.longitude
        except:
            pass
        return None, None

    # ----------------------------
    # 2: Top Cities by Subscribers (Map)
    # ----------------------------
    # ----------------------------
    # Bar Chart: Top 20 Cities by Active Subscribers
    # ----------------------------
    st.subheader("🏙️ Top 20 Cities by Active Subscribers")

    # Group by city
    subByCity = (
        current.groupby("City")["AccoutID"]
        .nunique()
        .sort_values(ascending=False)
        .head(20)
    )

    # Convert to dataframe
    city_df = subByCity.reset_index()
    city_df.columns = ["City", "Subscribers"]

    # Bar chart
    fig_bar = px.bar(
        city_df,
        x="Subscribers",
        y="City",
        orientation="h",
        color="Subscribers",
        color_continuous_scale="Blues",
        labels={"Subscribers": "Active Subscribers", "City": "City"},
        title="Top 20 Cities by Subscriber Count",
        height=650
    )

    fig_bar.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        margin=dict(l=20, r=20, t=60, b=20),
        coloraxis_showscale=False
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # ----------------------------
    # 3: Subscribers Over Time (Improved)
    # ----------------------------
    st.subheader("📈 Unique Subscribers Over Time")

    # Keep only rows with valid dates
    valid = data.dropna(subset=["LastStartDate"]).copy()

    # Extract monthly period
    valid["YearMonth"] = valid["LastStartDate"].dt.to_period("M")
    valid["YearMonth_dt"] = valid["YearMonth"].dt.to_timestamp()

    # Filter by date range
    valid = valid[valid["YearMonth_dt"] >= pd.Timestamp("2018-01-01")]

    # --- FIXED: Unique subscribers per month ---
    monthly = (
        valid.groupby("YearMonth_dt")["AccoutID"]
        .nunique()
        .sort_index()
    )

    # --- Create continuous monthly timeline (prevents spikes) ---
    all_months = pd.date_range(
        start=monthly.index.min(),
        end=monthly.index.max(),
        freq="MS"
    )

    monthly = monthly.reindex(all_months, fill_value=0)
    monthly.index.name = "YearMonth"

    # --- 3-month smoothing ---
    monthly_smooth = monthly.rolling(window=3, center=True).mean()

    # --- Final plotted figure ---
    fig3 = px.line(
        x=monthly.index,
        y=monthly.values,
        title="Unique Subscribers Over Time",
        labels={"x": "Year-Month", "y": "Unique Subscribers"},
    )

    # Add smooth line
    fig3.add_scatter(
        x=monthly_smooth.index,
        y=monthly_smooth.values,
        mode="lines",
        name="3-Month Moving Avg",
        line=dict(width=3, dash="dot")
    )

    fig3.update_layout(
        xaxis=dict(
            tickformat="%b\n%Y",
            dtick="M3",
            showgrid=True
        ),
        template="plotly_white",
        height=450
    )

    st.plotly_chart(fig3, use_container_width=True)

    # ----------------------------
    # 4: Subscribers Over Time by Subscription Type
    # ----------------------------
#     st.subheader("📈 Subscribers Over Time by Subscription Type")
#
#     subsTimeType = (
#         valid.groupby(["YearMonth", "SubType"])["AccoutID"]
#         .nunique()
#         .reset_index()
#     )
#
#     pivot = subsTimeType.pivot(
#         index="YearMonth",
#         columns="SubType",
#         values="AccoutID"
#     ).fillna(0)
#
#     fig4 = px.line(
#         pivot,
#         x=pivot.index.astype(str),
#         y=pivot.columns,
#         labels={"x": "Year-Month", "value": "Subscribers"},
#     )
#     st.plotly_chart(fig4, use_container_width=True)
#
# else:
#     st.info("Upload one or more CSV/XLSX files to begin.")


# ----------------------------
# 4: Subscribers Over Time by Subscription Type (Improved)
# ----------------------------
st.subheader("📈 Subscribers Over Time by Subscription Type")

# Aggregate unique subscribers per month per type
subsTimeType = (
    valid.groupby(["YearMonth_dt", "SubType"])["AccoutID"]
    .nunique()
    .reset_index()
)

# Create continuous monthly index
all_months = pd.date_range(
    start=subsTimeType["YearMonth_dt"].min(),
    end=subsTimeType["YearMonth_dt"].max(),
    freq="MS"
)

# Pivot and reindex to create uniform monthly timeline
pivot = subsTimeType.pivot(
    index="YearMonth_dt",
    columns="SubType",
    values="AccoutID"
).reindex(all_months).fillna(0)

pivot.index.name = "YearMonth"

# Optional: 3-month smoothing
pivot_smooth = pivot.rolling(3, center=True).mean()

# Define a clean color palette
color_map = {
    "Digital": "#1f77b4",   # blue
    "Print": "#ff7f0e",     # orange
    "Bundle": "#2ca02c",    # green
    "Other": "#d62728",     # red
}

fig4 = px.line(
    pivot,
    x=pivot.index,
    y=pivot.columns,
    color_discrete_map=color_map,
    labels={"value": "Subscribers", "YearMonth": "Year-Month"},
    title="Subscribers Over Time by Subscription Type"
)

# Add smoothed lines as dotted overlays
for col in pivot.columns:
    fig4.add_scatter(
        x=pivot_smooth.index,
        y=pivot_smooth[col],
        mode="lines",
        name=f"{col} (3-mo avg)",
        line=dict(width=3, dash="dot", color=color_map[col]),
        showlegend=False  # or True if you want them separate
    )

fig4.update_layout(
    template="plotly_white",
    height=500,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    xaxis=dict(
        tickformat="%b\n%Y",
        dtick="M3",
        showgrid=True
    )
)

st.plotly_chart(fig4, use_container_width=True)
