import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

from utils.auth import (
    require_login,
    get_current_role,
    get_current_name
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Commodity & Stock Management",
    page_icon="📦",
    layout="wide"
)

require_login()


# =========================================================
# ROLE INFORMATION
# =========================================================

current_role = get_current_role()
current_name = get_current_name()

COMMODITY_VIEW_ROLES = [
    "FP Service Provider",
    "Pharmacy/Commodity Officer",
    "Supervisor",
    "Administrator"
]

COMMODITY_EDIT_ROLES = [
    "Pharmacy/Commodity Officer",
    "Supervisor",
    "Administrator"
]

if current_role not in COMMODITY_VIEW_ROLES:

    st.error(
        "⛔ You do not have permission to access "
        "Commodity & Stock Management."
    )

    st.stop()

can_edit_commodities = current_role in COMMODITY_EDIT_ROLES


# =========================================================
# FILE CONFIGURATION
# =========================================================

STOCK_FILE = Path("data/commodity_stock.csv")

EXPECTED_COLUMNS = [
    "date",
    "commodity",
    "opening_stock",
    "stock_received",
    "quantity_dispensed",
    "losses_adjustments",
    "closing_stock",
    "stock_out",
    "stock_out_days"
]


# =========================================================
# COMMODITY LIST
# =========================================================

commodities = [
    "Male Condoms",
    "Female Condoms",
    "DMPA-IM",
    "DMPA-SC",
    "Combined Oral Contraceptive Pills",
    "Progestin Only Pills",
    "Emergency Contraception",
    "Implant 1 Rod",
    "Implant 2 Rods",
    "IUCD"
]


# =========================================================
# PAGE STYLING
# =========================================================

st.markdown(
    """
    <style>

    .section-card {
        padding: 1rem 1.2rem;
        border: 1px solid #d9d9d9;
        border-radius: 10px;
        margin-bottom: 1rem;
        background-color: #ffffff;
    }

    .role-note {
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid #d9d9d9;
        background-color: #f7f7f7;
        margin-bottom: 1rem;
    }

    .stock-table-wrapper {
        width: 100%;
        overflow-x: auto;
        margin: 0.5rem 0 1.2rem 0;
        border: 1px solid #d9d9d9;
        border-radius: 8px;
        background: #ffffff;
    }

    .stock-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }

    .stock-table th {
        text-align: left;
        padding: 10px 12px;
        border-bottom: 2px solid #d9d9d9;
        background: #f5f7f9;
        font-weight: 700;
        white-space: nowrap;
    }

    .stock-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #e5e5e5;
        white-space: nowrap;
    }

    .stock-table tbody tr:last-child td {
        border-bottom: none;
    }

    .stock-table tbody tr:hover {
        background: #f8f9fa;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# DATA FUNCTIONS
# =========================================================

def load_stock_data():

    if not STOCK_FILE.exists():

        return pd.DataFrame(
            columns=EXPECTED_COLUMNS
        )

    dataframe = pd.read_csv(STOCK_FILE)

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    dataframe = dataframe[
        EXPECTED_COLUMNS
    ].copy()

    numeric_columns = [
        "opening_stock",
        "stock_received",
        "quantity_dispensed",
        "losses_adjustments",
        "closing_stock",
        "stock_out_days"
    ]

    for column in numeric_columns:

        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce"
        ).fillna(0)

    return dataframe


def get_latest_closing_stock(dataframe, selected_commodity):

    if dataframe.empty:
        return 0

    commodity_records = dataframe[
        dataframe["commodity"] == selected_commodity
    ].copy()

    if commodity_records.empty:
        return 0

    commodity_records["date_sort"] = pd.to_datetime(
        commodity_records["date"],
        errors="coerce"
    )

    commodity_records = commodity_records.sort_values(
        by="date_sort"
    )

    latest_record = commodity_records.iloc[-1]

    return int(latest_record["closing_stock"])


def display_stock_table(dataframe):

    if dataframe.empty:

        st.info(
            "No stock records have been entered yet."
        )

        return

    html_table = dataframe.to_html(
        index=False,
        escape=True,
        classes="stock-table",
        border=0
    )

    st.markdown(
        f"""
        <div class="stock-table-wrapper">
            {html_table}
        </div>
        """,
        unsafe_allow_html=True
    )


stock_df = load_stock_data()


# =========================================================
# PAGE HEADER
# =========================================================

st.title(
    "📦 Commodity & Stock Management"
)

st.subheader(
    "Njoro Sub-County Hospital"
)

st.write(
    "Monitor family planning commodity stock movements, "
    "available stock and potential stock-outs."
)

st.caption(
    f"Logged in as: {current_name} | "
    f"Role: {current_role}"
)


if not can_edit_commodities:

    st.info(
        "👁️ You have view-only access to commodity records. "
        "Stock transactions can be entered by authorized "
        "Pharmacy/Commodity, Supervisor or Administrator users."
    )


st.divider()


# =========================================================
# STOCK SUMMARY
# =========================================================

st.subheader(
    "Stock Summary"
)

total_received = stock_df[
    "stock_received"
].sum()

total_dispensed = stock_df[
    "quantity_dispensed"
].sum()

latest_stock_by_commodity = (
    stock_df
    .sort_values("date")
    .groupby("commodity", as_index=False)
    .tail(1)
)

total_closing_stock = latest_stock_by_commodity[
    "closing_stock"
].sum()

total_stock_outs = (
    stock_df["stock_out"]
    .astype(str)
    .str.lower()
    .eq("yes")
    .sum()
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Total Stock Received",
        int(total_received)
    )

with col2:

    st.metric(
        "Total Quantity Dispensed",
        int(total_dispensed)
    )

with col3:

    st.metric(
        "Current Recorded Stock",
        int(total_closing_stock)
    )

with col4:

    st.metric(
        "Stock-Out Records",
        int(total_stock_outs)
    )


st.divider()


# =========================================================
# STOCK TRANSACTION FORM
# =========================================================

if can_edit_commodities:

    st.subheader(
        "Record Stock Transaction"
    )

    # ---------------------------------------------------------
    # COMMODITY SELECTION
    # ---------------------------------------------------------

    commodity = st.selectbox(
        "Commodity",
        commodities,
        key="stock_commodity_selector"
    )

    latest_closing_stock = get_latest_closing_stock(
        stock_df,
        commodity
    )

    st.caption(
        f"Latest recorded closing stock for {commodity}: "
        f"**{latest_closing_stock}**"
    )

    with st.form("stock_form"):

        col1, col2 = st.columns(2)

        with col1:

            transaction_date = st.date_input(
                "Transaction Date",
                value=date.today()
            )

            opening_stock = st.number_input(
                "Opening Stock",
                min_value=0,
                value=latest_closing_stock,
                step=1,
                disabled=True,
                help=(
                    "Automatically carried forward from the "
                    "latest recorded closing stock for the "
                    "selected commodity."
                )
            )

            stock_received = st.number_input(
                "Stock Received",
                min_value=0,
                step=1
            )

        with col2:

            quantity_dispensed = st.number_input(
                "Quantity Dispensed",
                min_value=0,
                step=1
            )

            losses_adjustments = st.number_input(
                "Losses / Adjustments",
                min_value=0,
                step=1
            )

            stock_out_days = st.number_input(
                "Stock-Out Days",
                min_value=0,
                step=1
            )

            stock_out = st.selectbox(
                "Stock-Out Status",
                ["No", "Yes"]
            )

        submitted = st.form_submit_button(
            "Save Stock Record",
            width="stretch"
        )

        if submitted:

            # -------------------------------------------------
            # PREVENT EMPTY / ZERO TRANSACTIONS
            # -------------------------------------------------

            if (
                opening_stock == 0
                and stock_received == 0
                and quantity_dispensed == 0
                and losses_adjustments == 0
                and stock_out == "No"
                and stock_out_days == 0
            ):

                st.error(
                    "Please enter at least one stock movement "
                    "or adjustment before saving the transaction."
                )

            else:

                closing_stock = (
                    opening_stock
                    + stock_received
                    - quantity_dispensed
                    - losses_adjustments
                )

                # ---------------------------------------------
                # VALIDATION
                # ---------------------------------------------

                if closing_stock < 0:

                    st.error(
                        "Closing stock cannot be negative. "
                        "Please check the quantities entered."
                    )

                elif (
                    stock_out == "No"
                    and stock_out_days > 0
                ):

                    st.error(
                        "Stock-Out Status is 'No', but Stock-Out Days "
                        "is greater than zero. Please correct the entry."
                    )

                elif (
                    stock_out == "Yes"
                    and stock_out_days == 0
                ):

                    st.error(
                        "Stock-Out Status is 'Yes', but Stock-Out Days "
                        "is zero. Please enter the number of stock-out days."
                    )

                else:

                    new_record = pd.DataFrame([{
                        "date": transaction_date.strftime(
                            "%Y-%m-%d"
                        ),

                        "commodity": commodity,

                        "opening_stock": opening_stock,

                        "stock_received": stock_received,

                        "quantity_dispensed":
                            quantity_dispensed,

                        "losses_adjustments":
                            losses_adjustments,

                        "closing_stock":
                            closing_stock,

                        "stock_out":
                            stock_out,

                        "stock_out_days":
                            stock_out_days
                    }])

                    stock_df = pd.concat(
                        [
                            stock_df,
                            new_record
                        ],
                        ignore_index=True
                    )

                    stock_df.to_csv(
                        STOCK_FILE,
                        index=False
                    )

                    st.success(
                        f"Stock record saved successfully. "
                        f"Closing stock: {int(closing_stock)}"
                    )


    st.divider()


# =========================================================
# STOCK REGISTER
# =========================================================

st.subheader(
    "Current Stock Register"
)

if not stock_df.empty:

    display_df = stock_df.copy()

    display_df["date"] = pd.to_datetime(
        display_df["date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    display_df = display_df.rename(
        columns={
            "date": "Date",
            "commodity": "Commodity",
            "opening_stock": "Opening Stock",
            "stock_received": "Stock Received",
            "quantity_dispensed": "Quantity Dispensed",
            "losses_adjustments": "Losses / Adjustments",
            "closing_stock": "Closing Stock",
            "stock_out": "Stock-Out",
            "stock_out_days": "Stock-Out Days"
        }
    )

    display_stock_table(
        display_df
    )

else:

    st.info(
        "No stock records have been entered yet. "
        "Authorized users can use the transaction form "
        "to record the first stock movement."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Family Planning Management System | "
    "Njoro Sub-County Hospital | "
    "Commodity & Stock Management"
)
