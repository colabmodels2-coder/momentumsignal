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
# File uploader (MUST NOT be cached)
# ============================
uploaded_file = st.file_uploader(
    "Upload Momentum Signal Excel file",
    type=["xlsx"]
)

if uploaded_file is None:
    st.stop()

@st.cache_data(show_spinner=False)
def cached_load(file):
    return load_all_data(file)

(
    country_ts,
    signal,
    signal_perf,
    s1,
    s2,
    s3,
    score_filter,
) = cached_load(uploaded_file)

# ============================
# Page navigation
# ============================
page = st.sidebar.radio(
    "Page",
    ["Performance", "Signals", "Signal Summary"]
)

# =====================================================
# PERFORMANCE PAGE (RESTORED)
# =====================================================
if page == "Performance":

    st.sidebar.header("Controls")

    strategy_options = sorted(signal_perf["strategy"].unique())
    default_strategy = "Top5" if "Top5" in strategy_options else strategy_options[0]
    strategy = st.sidebar.selectbox("Strategy", strategy_options)

    perf = signal_perf[signal_perf["strategy"] == strategy].copy()

    st.subheader("📌 Current Signal")

    latest_date = signal["date"].max()
    current_signal = signal[signal["date"] == latest_date].sort_values("rank")

    st.write(f"**As of:** {latest_date.date()}")
    st.dataframe(
        current_signal[["rank", "country"]],
        hide_index=True,
        use_container_width=True
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
# SIGNALS PAGE (DATE LABELS CLEAN)
# =====================================================
if page == "Signals":

    st.header("🔍 Signal Oversight")

    countries = [c for c in country_ts.columns if c != "date"]
    country = st.selectbox("Select Country", sorted(countries))

    end_date = country_ts["date"].max()
    start_date = end_date - pd.DateOffset(months=36)

    def sl(df):
        return df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    ts = sl(country_ts)
    s1_ = sl(s1)
    s2_ = sl(s2)
    s3_ = sl(s3)
    sc = sl(score_filter)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.plot(ts["date"], ts[country], label="TR", lw=2)
        ax.plot(s1_["date"], s1_[country], "--", label="S1")
        ax.plot(s2_["date"], s2_[country], "--", label="S2")
        ax.plot(s3_["date"], s3_[country], "--", label="S3")
        ax.legend()
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.plot(sc["date"], sc[country], color="black", lw=2)
        ax.axhline(0, color="red", ls="--")
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        st.pyplot(fig)

# =====================================================
# SIGNAL SUMMARY PAGE (COLOUR FIXED PROPERLY)
# =====================================================
if page == "Signal Summary":

    st.header("📊 Signal Summary – Cross‑Section")

    latest_date = score_filter["date"].max()

    summary = pd.DataFrame({
        "score": score_filter.set_index("date").loc[latest_date],
        "tr": country_ts.set_index("date").loc[latest_date],
        "s1": s1.set_index("date").loc[latest_date],
        "s2": s2.set_index("date").loc[latest_date],
        "s3": s3.set_index("date").loc[latest_date],
    })

    # ✅ Explicit rule: RED if TR <= any MA
    summary["pass_trend"] = (
        (summary["tr"] > summary["s1"]) &
        (summary["tr"] > summary["s2"]) &
        (summary["tr"] > summary["s3"])
    )

    summary = summary.dropna(subset=["score"]).sort_values("score")

    colours = ["tab:blue" if x else "red" for x in summary["pass_trend"]]

    fig, ax = plt.subplots(figsize=(8, max(6, len(summary) * 0.25)))
    ax.barh(summary.index, summary["score"], color=colours)

    ax.set_title(f"Score Filter with Trend Confirmation – {latest_date.date()}")
    ax.set_xlabel("Score")
    ax.set_ylabel("Country")
    ax.grid(axis="x", alpha=0.5)

    st.pyplot(fig)
