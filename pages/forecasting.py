import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import Holt

from utils.auth import require_role, get_current_role, get_current_name


st.set_page_config(
    page_title="Demand Forecasting",
    page_icon="📈",
    layout="wide"
)


# --------------------------------------------------
# Role-based access
# --------------------------------------------------

FORECAST_VIEW_ROLES = [
    "FP Service Provider",
    "Pharmacy/Commodity Officer",
    "Supervisor",
    "Administrator"
]

require_role(FORECAST_VIEW_ROLES)

current_role = get_current_role()
current_name = get_current_name()


# --------------------------------------------------
# Load service data
# --------------------------------------------------

DATA_PATH = "data/service_records.csv"
STOCK_PATH = "data/commodity_stock.csv"



def load_stock_data():
    """Load the current commodity stock register for early-warning analysis."""

    expected_columns = [
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

    try:
        stock = pd.read_csv(STOCK_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=expected_columns)

    missing_columns = [
        column
        for column in expected_columns
        if column not in stock.columns
    ]

    if missing_columns:
        return pd.DataFrame(columns=expected_columns)

    stock["date"] = pd.to_datetime(
        stock["date"],
        errors="coerce"
    )

    stock["commodity"] = stock["commodity"].astype(str)

    stock["closing_stock"] = pd.to_numeric(
        stock["closing_stock"],
        errors="coerce"
    )

    stock = stock.dropna(
        subset=[
            "date",
            "commodity",
            "closing_stock"
        ]
    ).copy()

    return stock


@st.cache_data
def load_data():

    data = pd.read_csv(DATA_PATH)

    data["month"] = pd.to_datetime(
        data["month"],
        format="%Y-%m",
        errors="coerce"
    )

    data["quantity_dispensed"] = pd.to_numeric(
        data["quantity_dispensed"],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "month",
            "method",
            "quantity_dispensed"
        ]
    )

    return data


df = load_data()


# --------------------------------------------------
# Page header
# --------------------------------------------------

st.title("📈 Family Planning Demand Forecasting")
st.subheader("Njoro Sub-County Hospital")

st.write(
    "This module analyzes historical family planning commodity "
    "consumption, compares forecasting models using historical "
    "backtesting, and estimates near-term commodity demand "
    "to support proactive commodity planning."
)


# --------------------------------------------------
# Role information
# --------------------------------------------------

if current_role in [
    "FP Service Provider",
    "Pharmacy/Commodity Officer"
]:

    st.info(
        f"👁️ View-only access | Logged in as {current_name} "
        f"({current_role})."
    )


# --------------------------------------------------
# Prepare monthly consumption
# --------------------------------------------------

monthly_consumption = (
    df.groupby(
        ["month", "method"]
    )["quantity_dispensed"]
    .sum()
    .reset_index()
)


# --------------------------------------------------
# Commodity selector
# --------------------------------------------------

commodities = sorted(
    monthly_consumption["method"].unique()
)

selected_commodity = st.selectbox(
    "Select Family Planning Commodity",
    commodities
)

st.markdown("### Planning Parameters")

PLANNING_COVERAGE_THRESHOLD_MONTHS = st.number_input(
    "Minimum Planning Stock Coverage (months)",
    min_value=0.5,
    max_value=3.0,
    value=1.0,
    step=0.5,
    help=(
        "Configurable planning threshold used for early-warning analysis. "
        "This is a system planning rule and is not presented as an official "
        "Njoro Sub-County Hospital policy."
    )
)

st.caption(
    "The threshold can be adjusted according to approved facility "
    "reorder levels, safety-stock requirements, supplier lead time "
    "or other commodity-management policies."
)


commodity_data = monthly_consumption[
    monthly_consumption["method"] == selected_commodity
].copy()

commodity_data = commodity_data.sort_values("month")


# --------------------------------------------------
# Use observed monthly consumption
# --------------------------------------------------

commodity_data["quantity_dispensed"] = pd.to_numeric(
    commodity_data["quantity_dispensed"],
    errors="coerce"
)

commodity_data = commodity_data.dropna(
    subset=["month", "quantity_dispensed"]
).copy()

commodity_data["method"] = selected_commodity


values = (
    commodity_data["quantity_dispensed"]
    .astype(float)
    .to_numpy()
)


# --------------------------------------------------
# Forecasting functions
# --------------------------------------------------

def historical_average_forecast(train_values):

    return float(
        np.mean(train_values)
    )


def linear_regression_forecast(train_values):

    y = np.asarray(
        train_values,
        dtype=float
    )

    x = np.arange(
        len(y)
    ).reshape(-1, 1)

    next_x = np.array(
        [[len(y)]]
    )

    model = LinearRegression()

    model.fit(
        x,
        y
    )

    prediction = model.predict(
        next_x
    )[0]

    return float(
        max(0, prediction)
    )


def holt_forecast(train_values):

    y = np.asarray(
        train_values,
        dtype=float
    )

    if len(y) < 3:
        return float(
            max(0, y[-1])
        )

    try:

        model = Holt(
            y,
            initialization_method="estimated"
        )

        fitted_model = model.fit(
            optimized=True
        )

        prediction = fitted_model.forecast(
            1
        )[0]

        return float(
            max(0, prediction)
        )

    except Exception:

        return float(
            max(0, y[-1])
        )


# --------------------------------------------------
# Error metrics
# --------------------------------------------------

def calculate_metrics(
    actual,
    predicted
):

    actual = np.asarray(
        actual,
        dtype=float
    )

    predicted = np.asarray(
        predicted,
        dtype=float
    )

    errors = actual - predicted

    mae = np.mean(
        np.abs(errors)
    )

    rmse = np.sqrt(
        np.mean(
            errors ** 2
        )
    )

    return mae, rmse


# --------------------------------------------------
# Backtesting
# --------------------------------------------------

def backtest_model(
    values,
    forecast_function
):

    actual_values = []
    predicted_values = []

    minimum_training_points = 3

    if len(values) <= minimum_training_points:

        return np.nan, np.nan

    for test_index in range(
        minimum_training_points,
        len(values)
    ):

        train_values = values[
            :test_index
        ]

        actual_value = values[
            test_index
        ]

        try:

            prediction = forecast_function(
                train_values
            )

            actual_values.append(
                actual_value
            )

            predicted_values.append(
                prediction
            )

        except Exception:

            continue

    if not actual_values:

        return np.nan, np.nan

    return calculate_metrics(
        actual_values,
        predicted_values
    )


# --------------------------------------------------
# Model definitions
# --------------------------------------------------

models = {
    "Historical Average":
        historical_average_forecast,

    "Linear Regression":
        linear_regression_forecast,

    "Holt Exponential Smoothing":
        holt_forecast
}


# --------------------------------------------------
# Run model evaluation
# --------------------------------------------------

model_results = []


for model_name, model_function in models.items():

    mae, rmse = backtest_model(
        values,
        model_function
    )

    model_results.append(
        {
            "Model": model_name,
            "MAE": mae,
            "RMSE": rmse
        }
    )


model_results_df = pd.DataFrame(
    model_results
)


valid_results = model_results_df.dropna(
    subset=["MAE", "RMSE"]
)


# --------------------------------------------------
# Select best model
# --------------------------------------------------

if valid_results.empty:

    selected_model_name = "Historical Average"

else:

    selected_model_name = (
        valid_results
        .sort_values(
            by=["MAE", "RMSE"]
        )
        .iloc[0]["Model"]
    )


selected_model_function = models[
    selected_model_name
]


# --------------------------------------------------
# Next-month forecast
# --------------------------------------------------

next_month_forecast = (
    selected_model_function(values)
)

next_month_forecast = round(
    max(0, next_month_forecast)
)


# --------------------------------------------------
# Early-warning stock risk analysis
# --------------------------------------------------

stock_data = load_stock_data()

commodity_stock = stock_data[
    stock_data["commodity"] == selected_commodity
].copy()

current_stock = None
stock_record_date = None
projected_stock = None
stock_coverage_months = None
stock_risk_status = "Stock data unavailable"
stock_action = (
    "Enter a current stock transaction for this commodity "
    "to enable stock-risk monitoring."
)

if not commodity_stock.empty:

    commodity_stock = commodity_stock.sort_values(
        by="date"
    )

    latest_stock_record = commodity_stock.iloc[-1]

    current_stock = int(
        latest_stock_record["closing_stock"]
    )

    stock_record_date = latest_stock_record["date"]

    projected_stock = (
        current_stock - next_month_forecast
    )

    if next_month_forecast > 0:

        stock_coverage_months = (
            current_stock / next_month_forecast
        )

    else:

        stock_coverage_months = None

    if current_stock <= 0:

        stock_risk_status = "🔴 Stock-out"

        stock_action = (
            "Review the stock-out immediately and "
            "initiate appropriate replenishment or redistribution."
        )

    elif projected_stock <= 0:

        stock_risk_status = "🔴 Projected Stock-out"

        stock_action = (
            "Review replenishment or redistribution before "
            "the expected demand period."
        )

    elif (
        stock_coverage_months is not None
        and stock_coverage_months < PLANNING_COVERAGE_THRESHOLD_MONTHS
    ):

        stock_risk_status = "🟠 Low Stock Warning"

        stock_action = (
            "Review replenishment, pending orders, supplier "
            "lead time and safety-stock requirements."
        )

    else:

        stock_risk_status = "🟢 No Immediate Risk"

        stock_action = (
            "Continue routine monitoring and review the "
            "forecast together with lead time and safety stock."
        )


# --------------------------------------------------
# Forecast summary
# --------------------------------------------------

st.subheader("Forecast Summary")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Selected Model",
        selected_model_name
    )


with col2:

    st.metric(
        "Next-Month Forecast",
        f"{next_month_forecast} units"
    )


with col3:

    st.metric(
        "Historical Months",
        len(commodity_data)
    )


with col4:

    selected_result = model_results_df[
        model_results_df["Model"]
        == selected_model_name
    ]

    if not selected_result.empty:

        selected_mae = selected_result[
            "MAE"
        ].iloc[0]

        st.metric(
            "Model MAE",
            f"{selected_mae:.2f}"
        )

    else:

        st.metric(
            "Model MAE",
            "N/A"
        )


# --------------------------------------------------
# Model selection explanation
# --------------------------------------------------

st.subheader("Model Selection")


st.success(
    f"🏆 **Selected model: {selected_model_name}**"
)


st.write(
    "The forecasting models were evaluated using historical "
    "backtesting. The model with the lowest Mean Absolute Error "
    "(MAE), with RMSE used as a secondary comparison, was selected "
    "for the next-month forecast."
)


# --------------------------------------------------
# Early-warning stock risk display
# --------------------------------------------------

st.subheader("Early-Warning Stock Risk")

st.caption(
    "This indicator compares the latest recorded stock with the "
    "forecasted next-month demand to identify potential stock "
    "shortage risk. It supports decision-making and does not "
    "automatically place orders."
)

if current_stock is None:

    unavailable_col1, unavailable_col2 = st.columns(2)

    with unavailable_col1:
        st.metric(
            "Stock Status",
            "⚪ Stock Data Unavailable"
        )

    with unavailable_col2:
        st.metric(
            "Forecast Demand",
            f"{next_month_forecast} units"
        )

    st.info(
        f"📋 Stock data is unavailable for **{selected_commodity}**. "
        "The system does not assume or fabricate a stock balance. "
        "Enter a stock transaction for this commodity to enable "
        "stock-risk monitoring."
    )

    st.caption(
        "The demand forecast remains available because it is based "
        "on historical service utilization. Stock-risk assessment "
        "requires a recorded stock balance."
    )

else:

    risk_col1, risk_col2, risk_col3 = st.columns(3)

    with risk_col1:

        st.metric(
            "Current Recorded Stock",
            f"{current_stock} units"
        )

    with risk_col2:

        st.metric(
            "Forecast Demand",
            f"{next_month_forecast} units"
        )

    with risk_col3:

        st.metric(
            "Projected Stock",
            f"{projected_stock} units"
        )

    coverage_col1, coverage_col2 = st.columns(2)

    with coverage_col1:

        if stock_coverage_months is not None:

            st.metric(
                "Estimated Stock Coverage",
                f"{stock_coverage_months:.2f} months"
            )

        else:

            st.metric(
                "Estimated Stock Coverage",
                "Not available"
            )

    with coverage_col2:

        st.metric(
            "Risk Status",
            stock_risk_status
        )

    if stock_record_date is not None:

        st.caption(
            "Latest stock record: "
            f"{stock_record_date.strftime('%Y-%m-%d')}"
        )

    st.caption(
        f"System planning threshold: "
        f"{PLANNING_COVERAGE_THRESHOLD_MONTHS:.1f} month of forecast coverage. "
        "This is a configurable planning rule and is not presented "
        "as an official Njoro Sub-County Hospital policy."
    )

    if projected_stock <= 0:

        st.error(
            f"⚠️ **{stock_risk_status}** — "
            f"projected demand would consume all available stock "
            f"or exceed it by {abs(projected_stock)} units."
        )

    elif (
        stock_coverage_months is not None
        and stock_coverage_months < PLANNING_COVERAGE_THRESHOLD_MONTHS
    ):

        st.warning(
            f"⚠️ **{stock_risk_status}** — "
            f"estimated stock coverage is only "
            f"{stock_coverage_months:.2f} months, below the "
            f"{PLANNING_COVERAGE_THRESHOLD_MONTHS:.1f}-month "
            "planning threshold."
        )

    else:

        st.success(
            f"✅ **{stock_risk_status}** — "
            f"{stock_coverage_months:.2f} months of forecast "
            "coverage are currently available."
        )

    st.markdown(
        f"**Recommended management action:** {stock_action}"
    )

    st.info(
        "Planning note: The early-warning indicator should be "
        "interpreted together with stock-out history, supplier "
        "lead time, safety-stock requirements, pending orders, "
        "and other operational factors. The planning threshold "
        "can be replaced with the facility's approved reorder "
        "level or minimum-stock policy when available."
    )


# --------------------------------------------------
# Model comparison table
# --------------------------------------------------

st.subheader(
    "Forecasting Model Comparison"
)


comparison_display = model_results_df.copy()


comparison_display["MAE"] = (
    comparison_display["MAE"]
    .round(2)
)


comparison_display["RMSE"] = (
    comparison_display["RMSE"]
    .round(2)
)


comparison_display = (
    comparison_display
    .sort_values(
        by=["MAE", "RMSE"]
    )
    .reset_index(drop=True)
)


comparison_html = comparison_display.to_html(
    index=False,
    escape=True,
    classes="fp-record-table",
    border=0,
)

st.markdown(
    f"""
    <div class="fp-table-wrapper">
        {comparison_html}
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Model interpretation
# --------------------------------------------------

st.subheader("Model Interpretation")


st.info(
    "Historical Average estimates future demand using the average "
    "of observed monthly consumption. Linear Regression estimates "
    "the next value from the historical time trend. Holt "
    "Exponential Smoothing gives greater weight to recent "
    "observations. The selected model is determined by historical "
    "prediction performance rather than model complexity."
)


# --------------------------------------------------
# Historical consumption table
# --------------------------------------------------

st.subheader(
    "Historical Monthly Consumption"
)


display_data = commodity_data.copy()


display_data["month"] = (
    display_data["month"]
    .dt.strftime("%Y-%m")
)


display_data = display_data.rename(
    columns={
        "month": "Month",
        "quantity_dispensed":
            "Quantity Dispensed"
    }
)


historical_html = display_data[
    [
        "Month",
        "Quantity Dispensed"
    ]
].to_html(
    index=False,
    escape=True,
    classes="fp-record-table",
    border=0,
)

st.markdown(
    f"""
    <div class="fp-table-wrapper">
        {historical_html}
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Historical consumption chart
# --------------------------------------------------

st.subheader(
    "Historical Consumption"
)


history_months = commodity_data[
    "month"
].tolist()


history_values = commodity_data[
    "quantity_dispensed"
].tolist()


fig = go.Figure()


fig.add_trace(
    go.Bar(
        x=history_months,
        y=history_values,
        name="Actual Consumption"
    )
)


fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Commodity Units",
    hovermode="x unified",
    legend_title="Measure"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# Forecast chart
# --------------------------------------------------

st.subheader(
    "Historical Consumption and Next-Month Forecast"
)


next_month = (
    commodity_data["month"].max()
    + pd.DateOffset(months=1)
)


forecast_fig = go.Figure()


forecast_fig.add_trace(
    go.Bar(
        x=history_months,
        y=history_values,
        name="Actual Consumption"
    )
)


forecast_fig.add_trace(
    go.Scatter(
        x=[
            history_months[-1],
            next_month
        ],
        y=[
            history_values[-1],
            next_month_forecast
        ],
        mode="lines+markers",
        name=f"{selected_model_name} Forecast"
    )
)


forecast_fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Commodity Units",
    hovermode="x unified",
    legend_title="Measure"
)


st.plotly_chart(
    forecast_fig,
    use_container_width=True
)


# --------------------------------------------------
# Forecast interpretation
# --------------------------------------------------

st.subheader(
    "Forecast Interpretation"
)


st.info(
    f"For **{selected_commodity}**, the system evaluated "
    f"{len(values)} monthly observations using three forecasting "
    f"approaches. Based on historical backtesting, "
    f"**{selected_model_name}** produced the lowest prediction "
    f"error and was therefore selected. The estimated demand for "
    f"the next month is **{next_month_forecast} units**."
)


# --------------------------------------------------
# Data limitation note
# --------------------------------------------------

st.subheader(
    "Data and Model Limitation"
)


st.warning(
    "The current dataset contains a relatively short historical "
    "period for each commodity. Forecast accuracy can improve as "
    "more monthly observations become available. The forecast "
    "should therefore be used as decision-support information "
    "together with current stock, stock receipts, losses or "
    "adjustments, stock-outs, lead time and other operational "
    "factors."
)


# --------------------------------------------------
# Planning note
# --------------------------------------------------

st.subheader(
    "Planning Note"
)


st.warning(
    "The forecasting model does not automatically place orders. "
    "It provides an estimate of expected demand to support "
    "proactive review of commodity availability and replenishment "
    "decisions by authorized staff."
)


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.caption(
    "Forecasting module | Family Planning Management System | "
    "Njoro Sub-County Hospital"
)
