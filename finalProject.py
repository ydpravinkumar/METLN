#
# import matplotlib.pyplot as plt
# import os
# import glob
# import openpyxl
# import streamlit as st
# import pandas as pd
# import plotly.express as px
#
# folderPath = "data"
# allFiles = glob.glob(os.path.join(folderPath, "*.xlsx"))
#
# dataframes = []
# for file in allFiles:
#     df = pd.read_excel(file)
#     df.columns = df.columns.str.strip()
#
#     if 'Legacy Acct ID' not in df.columns:
#         df['Legacy Acct ID'] = pd.NA
#
#     dataframes.append(df)
#
# data = pd.concat(dataframes,ignore_index=True)
#
# print(data.head())
# for col in ['LastStartDate','OriginalStartDate']:
#     data[col] = pd.to_datetime(data[col],errors='coerce')
#
# current = data[data['Status'].str.upper() == 'ACTIVE'].copy()
# data['YearMonth'] = data['LastStartDate'].dt.to_period('M')
# def classifySubscription(row):
#     billMethod = str(row['Bill Method']).upper()
#     rateCode = str(row['Rate Code']).upper()
#
#     if "DIGITAL" in billMethod or 'D' in rateCode:
#         return "Digital"
#     elif "PRINT" in billMethod or "P" in rateCode:
#         return "Print"
#     elif "BUNDLE" in billMethod or "B" in rateCode:
#         return "Bundle"
#     else:
#         return "Other"
#
# data['SubType'] = data.apply(classifySubscription,axis=1)
#
# current = data[data['Status'].str.upper() == 'ACTIVE'].copy()
#
# subsByState = current.groupby('State')['AccoutID'].nunique().sort_values(ascending=False)
# subByCity = current.groupby('City')['AccoutID'].nunique().sort_values(ascending=False)
# valid = data.dropna(subset=['LastStartDate']).copy()
# valid['YearMonth'] = valid['LastStartDate'].dt.to_period('M')
#
# subsOverTime = (
#     valid.groupby(['YearMonth', 'AccoutID'])
#     .size()
#     .reset_index(name='num_accounts')
# )
#
#
# subsTimeType = (
#     valid.groupby(['YearMonth', 'SubType'])['AccoutID']
#     .nunique()
#     .reset_index()
# )
#
# pivot = subsTimeType.pivot(index='YearMonth', columns='SubType', values='AccoutID').fillna(0)
#
# st.set_page_config(page_title="Subscription Dashboard", layout="wide")
#
# st.title("📊 Subscription Analytics Dashboard")
#
# # ----------------------------
# # Upload CSV
# # ----------------------------
# uploaded_file = st.file_uploader("Upload your dataset", type=["csv"])
#
# if uploaded_file:
#     data = pd.read_csv(uploaded_file, parse_dates=["LastStartDate"])
#
#     # Sidebar Filters
#     st.sidebar.header("Filters")
#
#     # STATUS FILTER
#     status_filter = st.sidebar.multiselect(
#         "Select Status",
#         options=data["Status"].str.upper().unique(),
#         default=["ACTIVE"]
#     )
#
#     # Filter data
#     current = data[data["Status"].str.upper().isin(status_filter)].copy()
#
#     st.subheader("Active Subscriptions by State")
#     subsByState = current.groupby("State")["AccoutID"].nunique().sort_values(ascending=False)
#
#     fig1 = px.bar(
#         subsByState.head(20),
#         x=subsByState.head(20).index,
#         y=subsByState.head(20).values,
#         labels={"x": "State", "y": "Number of Accounts"}
#     )
#     st.plotly_chart(fig1, use_container_width=True)
#
#     # ---------------------------------------------------------------
#     st.subheader("Top 20 Cities by Active Shareholders")
#     subByCity = current.groupby("City")["AccoutID"].nunique().sort_values(ascending=False)
#
#     fig2 = px.bar(
#         subByCity.head(20),
#         x=subByCity.head(20).index,
#         y=subByCity.head(20).values,
#         labels={"x": "City", "y": "Number of Accounts"},
#     )
#     st.plotly_chart(fig2, use_container_width=True)
#
#     # ---------------------------------------------------------------
#     st.subheader("Unique Subscribers Over Time")
#
#     valid = data.dropna(subset=["LastStartDate"]).copy()
#     valid["YearMonth"] = valid["LastStartDate"].dt.to_period("M")
#
#     subsOverTime = (
#         valid.groupby(["YearMonth", "AccoutID"])
#         .size()
#         .reset_index(name="num_accounts")
#     )
#
#     fig3 = px.line(
#         subsOverTime,
#         x=subsOverTime["YearMonth"].astype(str),
#         y="num_accounts",
#         labels={"x": "Year-Month", "num_accounts": "Number of Unique Accounts"},
#     )
#     st.plotly_chart(fig3, use_container_width=True)
#
#     # ---------------------------------------------------------------
#     st.subheader("Subscribers Over Time by Subscription Type")
#
#     subsTimeType = (
#         valid.groupby(["YearMonth", "SubType"])["AccoutID"]
#         .nunique()
#         .reset_index()
#     )
#     pivot = subsTimeType.pivot(index="YearMonth", columns="SubType", values="AccoutID").fillna(0)
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
#     st.info("Upload a CSV to begin.")


import streamlit as st
import pandas as pd
import plotly.express as px

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

    # # ----------------------------
    # # 1: Active Subs by State
    # # ----------------------------
    # st.subheader("Active Subscriptions by State")
    #
    # subsByState = (
    #     current.groupby("State")["AccoutID"]
    #     .nunique()
    #     .sort_values(ascending=False)
    # )
    #
    # fig1 = px.bar(
    #     subsByState.head(20),
    #     x=subsByState.head(20).index,
    #     y=subsByState.head(20).values,
    #     labels={"x": "State", "y": "Active Accounts"}
    # )
    #
    # st.plotly_chart(fig1, use_container_width=True)

    # ----------------------------
    # 2: Top Cities by Subscribers
    # ----------------------------
    st.subheader("Top 20 Cities by Active Subscribers")
    # print(current['City'].unique())

    subByCity = (
        current.groupby("City")["AccoutID"]
        .nunique()
        .sort_values(ascending=False)
    )



    fig2 = px.bar(
        subByCity.head(20),
        x=subByCity.head(20).index,
        y=subByCity.head(20).values,
        labels={"x": "City", "y": "Active Accounts"},
    )

    st.plotly_chart(fig2, use_container_width=True)

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

