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
# SIGNAL SUMMARY PAGE (FIXED TREND FILTER)
# =====================================================
if page == "Signal Summary":

    st.header("📊 Signal Summary – Cross‑Section")

    latest_date = score_filter["date"].max()

    scores = score_filter.set_index("date").loc[latest_date]
    tr = country_ts.set_index("date").loc[latest_date]
    s1v = s1.set_index("date").loc[latest_date]
    s2v = s2.set_index("date").loc[latest_date]
    s3v = s3.set_index("date").loc[latest_date]

    summary = pd.DataFrame({
        "score": scores,
        "tr": tr,
        "s1": s1v,
        "s2": s2v,
        "s3": s3v
    }).dropna()

    # ✅ Correct logic: RED if TR NOT above all three
    summary["pass_trend"] = (
        (summary["tr"] > summary["s1"]) &
        (summary["tr"] > summary["s2"]) &
        (summary["tr"] > summary["s3"])
    )

    summary = summary.sort_values("score", ascending=True)

    colours = summary["pass_trend"].map(lambda x: "tab:blue" if x else "red")

    fig, ax = plt.subplots(figsize=(8, max(6, len(summary) * 0.25)))
    ax.barh(summary.index, summary["score"], color=colours)

    ax.set_title(f"Score Filter with Trend Confirmation – {latest_date.date()}")
    ax.set_xlabel("Score")
    ax.set_ylabel("Country")
    ax.grid(axis="x", alpha=0.5)

    st.pyplot(fig)

# =====================================================
# SIGNALS PAGE (DATE LABELS FIXED)
# =====================================================
if page == "Signals":

    st.header("🔍 Signal Oversight")

    countries = [c for c in country_ts.columns if c != "date"]
    country = st.selectbox("Select country", sorted(countries))

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
        ax.plot(sc["date"], sc[country], color="black")
        ax.axhline(0, color="red", ls="--")
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        st.pyplot(fig)
