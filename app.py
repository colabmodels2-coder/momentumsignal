import streamlit as st
import pandas as pd

from src.data_loader import load_all_data
from src.performance import compute_cumulative_returns
from src.charts import (
    plot_cumulative_returns,
    plot_drawdowns,
    plot_rolling_returns,
    plot_return_distribution
)

st.set_page_config(
    page_title="EMD Signal Dashboard",
    layout="wide"
)

st.title("📊 EMD Systematic Signal Dashboard")

# ---------------------------
# Load data
# ---------------------------
country_ts, signal, signal_perf = load_all_data()

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.header("Controls")

strategy = st.sidebar.selectbox(
    "Strategy",
    options=signal_perf["strategy"].unique(),
    index=signal_perf["strategy"].tolist().index("Top5") if "Top5" in signal_perf["strategy"].values else 0
)

date_range = st.sidebar.date_input(
    "Date range",
    value=[
        signal_perf["date"].min(),
        signal_perf["date"].max()
    ]
)

# Filter performance
mask = (
    (signal_perf["strategy"] == strategy) &
    (signal_perf["date"] >= pd.to_datetime(date_range[0])) &
    (signal_perf["date"] <= pd.to_datetime(date_range[1]))
)

perf = signal_perf.loc[mask].copy()

# ---------------------------
# Current signal snapshot
# ---------------------------
st.subheader("📌 Current Signal (Top Assets)")

latest_date = signal["date"].max()
current_signal = (
    signal[signal["date"] == latest_date]
    .sort_values("rank")
)

st.write(f"**As of:** {latest_date.date()}")

st.dataframe(
    current_signal[["rank", "country"]],
    use_container_width=True,
    hide_index=True
)

# ---------------------------
# Performance analytics
# ---------------------------
st.subheader("📈 Strategy Performance")

cum_returns = compute_cumulative_returns(perf)

col1, col2 = st.columns(2)

with col1:
    st.pyplot(plot_cumulative_returns(cum_returns, strategy))

with col2:
    st.pyplot(plot_drawdowns(cum_returns))

# ---------------------------
# Rolling analytics
# ---------------------------
st.subheader("🔁 Rolling Analytics")

col3, col4 = st.columns(2)

with col3:
    st.pyplot(plot_rolling_returns(perf, window=12))

with col4:
    st.pyplot(plot_return_distribution(perf, window=12))
