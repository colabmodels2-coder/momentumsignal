import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.data_loader import load_all_data
from src.performance import compute_cumulative_returns
from src.charts import (
    plot_cumulative_returns,
    plot_drawdowns,
    plot_rolling_returns,
    plot_return_distribution,
)

# ============================
# Page setup
# ============================
st.set_page_config(
    page_title="Momentum Signal Dashboard",
    layout="wide"
)

st.title("📊 Momentum Signal Dashboard")

# ============================
# Load all data
# ============================
(
    country_ts,
    signal,
    signal_perf,
    s1,
    s2,
    s3,
    score_filter,
) = load_all_data()

# ============================
# Page navigation
# ============================
page = st.sidebar.radio(
    "Page",
    ["Performance", "Signals", "Signal Summary"]
)

# =====================================================
# PERFORMANCE PAGE
# =====================================================
if page == "Performance":

    st.sidebar.header("Controls")

    strategy_options = sorted(signal_perf["strategy"].unique())
    default_strategy = "Top5" if "Top5" in strategy_options else strategy_options[0]
    default_index = strategy_options.index(default_strategy)

    strategy = st.sidebar.selectbox(
        "Strategy",
        options=strategy_options,
        index=default_index
    )

    date_range = st.sidebar.date_input(
        "Date range",
        value=[
            signal_perf["date"].min(),
            signal_perf["date"].max()
        ]
    )

    perf = signal_perf[
        (signal_perf["strategy"] == strategy)
        & (signal_perf["date"] >= pd.to_datetime(date_range[0]))
        & (signal_perf["date"] <= pd.to_datetime(date_range[1]))
    ].copy()

    st.subheader("📌 Current Signal")

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

    st.subheader("📈 Strategy Performance")

    cum_perf = compute_cumulative_returns(perf)

    col1, col2 = st.columns(2)

    with col1:
        st.pyplot(plot_cumulative_returns(cum_perf, strategy))

    with col2:
        st.pyplot(plot_drawdowns(cum_perf))

    st.subheader("🔁 Rolling Analytics")

    col3, col4 = st.columns(2)

    with col3:
        st.pyplot(plot_rolling_returns(perf, window=12))

    with col4:
        st.pyplot(plot_return_distribution(perf, window=12))

# =====================================================
# SIGNALS PAGE (per‑country oversight)
# =====================================================
if page == "Signals":

    st.header("🔍 Signal Oversight")

    countries = [c for c in country_ts.columns if c != "date"]
    country = st.selectbox("Select country", sorted(countries))

    end_date = country_ts["date"].max()
    start_date = end_date - pd.DateOffset(months=36)

    def slice_df(df):
        return df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    ts = slice_df(country_ts)
    s1_ = slice_df(s1)
    s2_ = slice_df(s2)
    s3_ = slice_df(s3)
    score_ = slice_df(score_filter)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.plot(ts["date"], ts[country], label="Total Return", linewidth=2)
        ax.plot(s1_["date"], s1_[country], linestyle="--", label="S1")
        ax.plot(s2_["date"], s2_[country], linestyle="--", label="S2")
        ax.plot(s3_["date"], s3_[country], linestyle="--", label="S3")

        ax.set_title(f"{country} – TR & Moving Averages (36m)")
        ax.legend()
        ax.grid(True)

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.plot(score_["date"], score_[country], color="black", linewidth=2)
        ax.axhline(0, color="red", linestyle="--", alpha=0.6)

        ax.set_title(f"{country} – Score Filter (36m)")
        ax.grid(True)

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        st.pyplot(fig)

# =====================================================
# SIGNAL SUMMARY PAGE (cross‑sectional scores)
# =====================================================
if page == "Signal Summary":

    st.header("📊 Signal Summary – Cross‑Section")

    latest_date = score_filter["date"].max()

    score_snapshot = (
        score_filter
        .set_index("date")
        .loc[latest_date]
        .dropna()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8, max(6, len(score_snapshot) * 0.25)))

    ax.barh(
        score_snapshot.index,
        score_snapshot.values
    )

    ax.set_title(f"Score Filter – {latest_date.date()}")
    ax.set_xlabel("Score")
    ax.set_ylabel("Country")
    ax.grid(axis="x", alpha=0.5)

    st.pyplot(fig)
