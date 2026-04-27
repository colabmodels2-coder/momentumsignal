import streamlit as st
import pandas as pd

from src.data_loader import load_all_data
from src.performance import compute_cumulative_returns
from src.charts import (
    plot_cumulative_returns,
    plot_drawdowns,
    plot_rolling_returns,
    plot_return_distribution,
    plot_signal_trend,
    plot_score_filter
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
    ["Performance", "Signals"]
)

# =====================================================
# PERFORMANCE PAGE (existing functionality)
# =====================================================
if page == "Performance":

    st.sidebar.header("Controls")

    # Strategy selector (robust)
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

    # ----------------------------
    # Current signal snapshot
    # ----------------------------
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

    # ----------------------------
    # Performance charts
    # ----------------------------
    st.subheader("📈 Strategy Performance")

    cum_perf = compute_cumulative_returns(perf)

    col1, col2 = st.columns(2)

    with col1:
        st.pyplot(plot_cumulative_returns(cum_perf, strategy))

    with col2:
        st.pyplot(plot_drawdowns(cum_perf))

    # ----------------------------
    # Rolling analytics
    # ----------------------------
    st.subheader("🔁 Rolling Analytics")

    col3, col4 = st.columns(2)

    with col3:
        st.pyplot(plot_rolling_returns(perf, window=12))

    with col4:
        st.pyplot(plot_return_distribution(perf, window=12))

# =====================================================
# SIGNALS PAGE (new oversight view)
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

    st.caption(
        f"Showing last 36 months: {start_date.date()} → {end_date.date()}"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.pyplot(
            plot_signal_trend(
                ts["date"],
                ts[country],
                s1_[country],
                s2_[country],
                s3_[country],
                country
            )
        )

    with col2:
        st.pyplot(
            plot_score_filter(
                score_["date"],
                score_[country],
                country
            )
        )
