import os

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.auth import (
    get_current_name,
    get_current_role,
    logout,
    require_login,
)

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Family Planning Management System",
    page_icon="🏥",
    layout="wide",
)

require_login()

# --------------------------------------------------
# Load global styling
# --------------------------------------------------

CSS_PATH = "utils/style.css"

if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True,
        )

# --------------------------------------------------
# Sidebar - logged-in user
# --------------------------------------------------

with st.sidebar:
    st.markdown("### 👤 Logged-in User")

    st.write(get_current_name())

    st.caption(
        f"Role: {get_current_role()}"
    )

    st.divider()

    st.markdown("### 🏥 System")

    st.caption(
        "Family Planning Management System"
    )

    st.caption(
        "Njoro Sub-County Hospital"
    )

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):
        logout()
        st.rerun()

# --------------------------------------------------
# Data loading
# --------------------------------------------------

DATA_PATH = "data/service_records.csv"


@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)

    data["month"] = pd.to_datetime(
        data["month"],
        errors="coerce",
    )

    return data


df = load_data()

# --------------------------------------------------
# Header
# --------------------------------------------------

st.title(
    "🏥 Family Planning Management System"
)

st.subheader(
    "Njoro Sub-County Hospital"
)

st.write(
    "A data-driven system for family planning "
    "service monitoring, commodity management "
    "and demand forecasting."
)

st.divider()

# --------------------------------------------------
# Dashboard overview
# --------------------------------------------------

st.subheader("📊 Service Overview")

total_records = len(df)

new_clients = (
    df["client_type"] == "New"
).sum()

revisits = (
    df["client_type"] == "Revisit"
).sum()

female_clients = (
    df["sex"] == "Female"
).sum()

male_clients = (
    df["sex"] == "Male"
).sum()

first_ever_users = (
    df["first_ever_user"] == "Yes"
).sum()

# --------------------------------------------------
# KPI cards
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Service Records",
        total_records,
    )

with col2:
    st.metric(
        "New Clients",
        new_clients,
    )

with col3:
    st.metric(
        "Revisits",
        revisits,
    )

col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        "Female Clients",
        female_clients,
    )

with col5:
    st.metric(
        "Male Clients",
        male_clients,
    )

with col6:
    st.metric(
        "First-Ever FP Users",
        first_ever_users,
    )

st.divider()

# --------------------------------------------------
# Monthly utilization
# --------------------------------------------------

st.subheader(
    "📈 Monthly Family Planning Utilization"
)

monthly_utilization = (
    df.groupby(
        df["month"].dt.to_period("M")
    )
    .size()
    .reset_index(name="Records")
)

monthly_utilization["month"] = (
    monthly_utilization["month"]
    .astype(str)
)

fig_monthly = px.line(
    monthly_utilization,
    x="month",
    y="Records",
    markers=True,
    title="Monthly Service Utilization",
)

fig_monthly.update_layout(
    xaxis_title="Month",
    yaxis_title="Number of Records",
)

st.plotly_chart(
    fig_monthly,
    use_container_width=True,
)

# --------------------------------------------------
# Method utilization
# --------------------------------------------------

st.subheader(
    "📊 Family Planning Method Utilization"
)

method_utilization = (
    df["method"]
    .value_counts()
    .reset_index()
)

method_utilization.columns = [
    "Method",
    "Records",
]

fig_methods = px.bar(
    method_utilization,
    x="Method",
    y="Records",
    title="Utilization by Family Planning Method",
)

fig_methods.update_layout(
    xaxis_title="Family Planning Method",
    yaxis_title="Number of Records",
)

st.plotly_chart(
    fig_methods,
    use_container_width=True,
)

# --------------------------------------------------
# Commodity consumption
# --------------------------------------------------

st.subheader(
    "📦 Commodity Consumption"
)

commodity_consumption = (
    df.groupby("method")["quantity_dispensed"]
    .sum()
    .reset_index()
)

commodity_consumption.columns = [
    "Method",
    "Quantity Dispensed",
]

fig_commodities = px.bar(
    commodity_consumption,
    x="Method",
    y="Quantity Dispensed",
    title="Commodity Consumption by Method",
)

fig_commodities.update_layout(
    xaxis_title="Family Planning Method",
    yaxis_title="Quantity Dispensed",
)

st.plotly_chart(
    fig_commodities,
    use_container_width=True,
)

# --------------------------------------------------
# Recent service records
# --------------------------------------------------

st.subheader(
    "📋 Recent Service Records"
)

display_columns = [
    "month",
    "sex",
    "age",
    "client_type",
    "method",
    "visit_type_for_method",
    "quantity_dispensed",
]

recent_records = (
    df[display_columns]
    .tail(10)
    .copy()
)

recent_records["month"] = (
    recent_records["month"]
    .dt.strftime("%d %b %Y")
)

recent_records.columns = [
    "Date",
    "Sex",
    "Age",
    "Client Type",
    "FP Method",
    "Visit Type",
    "Quantity",
]

html_table = recent_records.to_html(
    index=False,
    escape=True,
    classes="fp-record-table",
    border=0,
)

st.markdown(
    f"""
    <div class="fp-table-wrapper">
        {html_table}
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "Family Planning Management System | "
    "Njoro Sub-County Hospital"
)
