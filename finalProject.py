
import matplotlib.pyplot as plt
import os
import glob
import openpyxl
import streamlit as st
import pandas as pd
import plotly.express as px

folderPath = "data"
allFiles = glob.glob(os.path.join(folderPath, "*.xlsx"))

dataframes = []
for file in allFiles:
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    if 'Legacy Acct ID' not in df.columns:
        df['Legacy Acct ID'] = pd.NA

    dataframes.append(df)

data = pd.concat(dataframes,ignore_index=True)

print(data.head())


for col in ['LastStartDate','OriginalStartDate']:
    data[col] = pd.to_datetime(data[col],errors='coerce')

current = data[data['Status'].str.upper() == 'ACTIVE'].copy()

data['YearMonth'] = data['LastStartDate'].dt.to_period('M')


def classifySubscription(row):
    billMethod = str(row['Bill Method']).upper()
    rateCode = str(row['Rate Code']).upper()

    if "DIGITAL" in billMethod or 'D' in rateCode:
        return "Digital"
    elif "PRINT" in billMethod or "P" in rateCode:
        return "Print"
    elif "BUNDLE" in billMethod or "B" in rateCode:
        return "Bundle"
    else:
        return "Other"

data['SubType'] = data.apply(classifySubscription,axis=1)

current = data[data['Status'].str.upper() == 'ACTIVE'].copy()

subsByState = current.groupby('State')['AccoutID'].nunique().sort_values(ascending=False)

# plt.figure(figsize=(10,10))
# subsByState.head(20).plot(kind='bar')
# plt.title('Active Subscriptions by State')
# plt.xlabel('State')
# plt.ylabel('Number of Accounts')
# plt.tight_layout()
# plt.show()


subByCity = current.groupby('City')['AccoutID'].nunique().sort_values(ascending=False)

# plt.figure(figsize=(10,10))
# subByCity.head(20).plot(kind='bar')
# plt.title('Top 20 cities by Active Shareholders')
# plt.xlabel('City')
# plt.ylabel('Number of Accounts')
# plt.tight_layout()
# plt.show()


valid = data.dropna(subset=['LastStartDate']).copy()
valid['YearMonth'] = valid['LastStartDate'].dt.to_period('M')

subsOverTime = (
    valid.groupby(['YearMonth', 'AccoutID'])
    .size()
    .reset_index(name='num_accounts')
)

# plt.figure(figsize=(10,10))
# plt.plot(subsOverTime['YearMonth'].astype(str), subsOverTime['num_accounts'])
# plt.xticks(rotation=45)
# plt.title('Unique Subscribers over time')
# plt.xlabel('Year-Month')
# plt.ylabel('Number of Unique Accounts')
# plt.tight_layout()
# plt.show()


subsTimeType = (
    valid.groupby(['YearMonth', 'SubType'])['AccoutID']
    .nunique()
    .reset_index()
)

pivot = subsTimeType.pivot(index='YearMonth', columns='SubType', values='AccoutID').fillna(0)


plt.figure(figsize=(10,10))
for col in pivot.columns:
    plt.plot(pivot.index.astype(str), pivot[col], label=col)
#
# plt.xticks(rotation=45)
# plt.title('Subscribers over time by Subscription Type')
# plt.xlabel('Year-Month')
# plt.ylabel('Number of Unique Accounts')
# plt.legend()
# plt.tight_layout()
# plt.show()





st.set_page_config(page_title="Subscription Dashboard", layout="wide")

st.title("📊 Subscription Analytics Dashboard")

# ----------------------------
# Upload CSV
# ----------------------------
uploaded_file = st.file_uploader("Upload your dataset", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file, parse_dates=["LastStartDate"])

    # Sidebar Filters
    st.sidebar.header("Filters")

    # STATUS FILTER
    status_filter = st.sidebar.multiselect(
        "Select Status",
        options=data["Status"].str.upper().unique(),
        default=["ACTIVE"]
    )

    # Filter data
    current = data[data["Status"].str.upper().isin(status_filter)].copy()

    st.subheader("Active Subscriptions by State")
    subsByState = current.groupby("State")["AccoutID"].nunique().sort_values(ascending=False)

    fig1 = px.bar(
        subsByState.head(20),
        x=subsByState.head(20).index,
        y=subsByState.head(20).values,
        labels={"x": "State", "y": "Number of Accounts"}
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------------------------------------------
    st.subheader("Top 20 Cities by Active Shareholders")
    subByCity = current.groupby("City")["AccoutID"].nunique().sort_values(ascending=False)

    fig2 = px.bar(
        subByCity.head(20),
        x=subByCity.head(20).index,
        y=subByCity.head(20).values,
        labels={"x": "City", "y": "Number of Accounts"},
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------------------
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
        labels={"x": "Year-Month", "num_accounts": "Number of Unique Accounts"},
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------------------------------------------
    st.subheader("Subscribers Over Time by Subscription Type")

    subsTimeType = (
        valid.groupby(["YearMonth", "SubType"])["AccoutID"]
        .nunique()
        .reset_index()
    )
    pivot = subsTimeType.pivot(index="YearMonth", columns="SubType", values="AccoutID").fillna(0)

    fig4 = px.line(
        pivot,
        x=pivot.index.astype(str),
        y=pivot.columns,
        labels={"x": "Year-Month", "value": "Subscribers"},
    )
    st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("Upload a CSV to begin.")
