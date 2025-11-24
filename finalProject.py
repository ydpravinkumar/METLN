import streamlit as st
import pandas as pd
import plotly.express as px
import geopy

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
    data["City"] = (
        data["City"]
        .astype(str)
        .str.strip()
        .str.title()
    )
    # Sidebar Filters
    st.sidebar.header("Filters")
    status_filter = st.sidebar.multiselect(
        "Select Status",
        options=data["Status"].str.upper().unique(),
        default=["ACTIVE"]
    )

    # Filter data
    current = data[data["Status"].str.upper().isin(status_filter)].copy()

    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="maine_map")


    @st.cache_data
    def get_coordinates(city):
        try:
            location = geolocator.geocode(f"{city}, Maine")
            if location:
                return location.latitude, location.longitude
        except:
            return None, None
        return None, None


    # 2: Top Cities by Subscribers
    # ----------------------------
    st.subheader("Top 20 Cities by Active Subscribers")
    # print(current['City'].unique())

    # subByCity = (
    #     current.groupby("City")["AccoutID"]
    #     .nunique()
    #     .sort_values(ascending=False)
    # )
    #
    #
    #
    # fig2 = px.bar(
    #     subByCity.head(20),
    #     x=subByCity.head(20).index,
    #     y=subByCity.head(20).values,
    #     labels={"x": "City", "y": "Active Accounts"},
    # )
    #
    # st.plotly_chart(fig2, use_container_width=True)

    # Group
    subByCity = (
        current.groupby("City")["AccoutID"]
        .nunique()
        .sort_values(ascending=False)
        .head(20)
    )

    # Convert to dataframe
    city_df = subByCity.reset_index()
    city_df.columns = ["City", "Subscribers"]

    # Add latitude/longitude
    latitudes = []
    longitudes = []

    for city in city_df["City"]:
        lat, lon = get_coordinates(city)
        latitudes.append(lat)
        longitudes.append(lon)

    city_df["Lat"] = latitudes
    city_df["Lon"] = longitudes

    # Drop empty coordinates
    city_df = city_df.dropna(subset=["Lat", "Lon"])

    # Plot the map
    fig = px.scatter_mapbox(
        city_df,
        lat="Lat",
        lon="Lon",
        size="Subscribers",
        color="Subscribers",
        hover_name="City",
        zoom=6.5,
        mapbox_style="carto-positron",
        height=600,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # 3: Subscribers Over Time
    # ----------------------------
    st.subheader("Unique Subscribers Over Time")

    valid = data.dropna(subset=["LastStartDate"]).copy()
    valid["YearMonth"] = valid["LastStartDate"].dt.to_period("M")

    subsOverTime = (
        valid.groupby(["YearMonth", "AccoutID"])
        .size()
        .reset_index(name="num_accounts")
    )

    fig3 = px.line(
        subsOverTime,
        x=subsOverTime["YearMonth"].astype(str),
        y="num_accounts",
        labels={"x": "Year-Month", "num_accounts": "Unique Subscribers"},
    )

    st.plotly_chart(fig3, use_container_width=True)

    # ----------------------------
    # Subscribers Over Time by Subscription Type (Separate Charts)
    # ----------------------------
    st.subheader("Subscribers Over Time by Subscription Type")

    subsTimeType = (
        valid.groupby(["YearMonth", "SubType"])["AccoutID"]
        .nunique()
        .reset_index()
    )

    # Convert YearMonth → string (for Plotly)
    subsTimeType["YearMonth"] = subsTimeType["YearMonth"].astype(str)

    sub_types = subsTimeType["SubType"].unique()

    # Display each subscription type as its own chart
    for subtype in sub_types:
        st.write(f"### {subtype} Subscribers Over Time")

        df_sub = subsTimeType[subsTimeType["SubType"] == subtype]

        fig = px.line(
            df_sub,
            x="YearMonth",
            y="AccoutID",
            labels={"YearMonth": "Year-Month", "AccoutID": "Subscribers"},
        )

        st.plotly_chart(fig, use_container_width=True)


else:
    st.info("Upload one or more CSV/XLSX files to begin.")

