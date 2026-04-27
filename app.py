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

# =====================================================
# Streamlit setup
# =====================================================

st.set_page_config(
    page_title="Momentum Signal Dashboard",
    layout="wide"
)

st.title("📊 Momentum Signal Dashboard")

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
    score_filter,   # unused here
    score,          # universe
) = cached_load(uploaded_file)

page = st.sidebar.radio(
    "Page",
    ["Performance", "Signals", "Signal Summary", "Diagnostics & Governance"]
)

# =====================================================
# PERFORMANCE PAGE
# =====================================================

if page == "Performance":

    st.sidebar.header("Controls")

    strategies = sorted(signal_perf["strategy"].unique())
    default = "Top5" if "Top5" in strategies else strategies[0]

    strategy = st.sidebar.selectbox(
        "Strategy",
        strategies,
        index=strategies.index(default)
    )

    perf = signal_perf[signal_perf["strategy"] == strategy]

    st.subheader("📌 Current Signal")

    latest_date = signal["date"].max()
    current_signal = signal[signal["date"] == latest_date].sort_values("rank")

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
# SIGNALS PAGE
# =====================================================

if page == "Signals":

    st.header("🔍 Signal Oversight")

    countries = [c for c in country_ts.columns if c != "date"]
    country = st.selectbox("Select country", sorted(countries))

    end = country_ts["date"].max()
    start = end - pd.DateOffset(months=36)

    def sl(df):
        return df[(df["date"] >= start) & (df["date"] <= end)]

    ts = sl(country_ts)
    s1_ = sl(s1)
    s2_ = sl(s2)
    s3_ = sl(s3)
    sc = sl(score)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.plot(ts["date"], ts[country], lw=2, label="TR")
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
        ax.plot(sc["date"], sc[country], lw=2)
        ax.axhline(0, color="red", linestyle="--")
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        st.pyplot(fig)

# =====================================================
# SIGNAL SUMMARY PAGE
# =====================================================

if page == "Signal Summary":

    st.header("📊 Signal Summary (Signal‑Date Aligned)")

    signal_dates = signal["date"].drop_duplicates().sort_values()

    selected_date = st.selectbox(
        "Select signal date",
        signal_dates,
        index=len(signal_dates) - 1,
        format_func=lambda d: d.strftime("%B %Y")
    )

    score_row = score.set_index("date").loc[selected_date]
    summary = pd.DataFrame({"Score": score_row})

    summary["TR"] = country_ts.set_index("date").loc[selected_date].reindex(summary.index)
    summary["S1"] = s1.set_index("date").loc[selected_date].reindex(summary.index)
    summary["S2"] = s2.set_index("date").loc[selected_date].reindex(summary.index)
    summary["S3"] = s3.set_index("date").loc[selected_date].reindex(summary.index)

    summary["Pass Trend"] = (
        (summary["TR"] > summary["S1"]) &
        (summary["TR"] > summary["S2"]) &
        (summary["TR"] > summary["S3"])
    )

    fails = summary[~summary["Pass Trend"]].sort_values("Score")
    passes = summary[summary["Pass Trend"]].sort_values("Score")

    plot_df = pd.concat([fails, passes])
    colours = ["#d62728"] * len(fails) + ["#1f77b4"] * len(passes)

    fig, ax = plt.subplots(figsize=(9, max(6, 0.28 * len(plot_df))))
    ax.barh(plot_df.index, plot_df["Score"], color=colours)
    ax.set_title(f"Score vs Trend Confirmation — {selected_date.strftime('%B %Y')}")
    ax.set_xlabel("Score")
    ax.grid(axis="x")
    st.pyplot(fig)

# =====================================================
# DIAGNOSTICS & GOVERNANCE PAGE
# =====================================================

if page == "Diagnostics & Governance":

    st.header("🧭 Diagnostics & Governance")

    signal_dates = signal["date"].drop_duplicates().sort_values()

    selected_date = st.selectbox(
        "Select signal date",
        signal_dates,
        index=len(signal_dates) - 1,
        format_func=lambda d: d.strftime("%B %Y")
    )

    st.caption(f"Diagnostics evaluated as of {selected_date.date()}")

    # -------------------------------------------------
    # 2A — Why is a country failing?
    # -------------------------------------------------
    st.subheader("1️⃣ Why is a country failing the trend filter?")

    diag = pd.DataFrame(index=score.columns)
    diag["TR"] = country_ts.set_index("date").loc[selected_date]
    diag["S1"] = s1.set_index("date").loc[selected_date]
    diag["S2"] = s2.set_index("date").loc[selected_date]
    diag["S3"] = s3.set_index("date").loc[selected_date]

    def fail_reason(r):
        if r["TR"] <= r["S1"]:
            return "S1"
        if r["TR"] <= r["S2"]:
            return "S2"
        if r["TR"] <= r["S3"]:
            return "S3"
        return "Pass"

    diag["Status"] = diag.apply(
        lambda r: "Pass" if (
            r["TR"] > r["S1"] and r["TR"] > r["S2"] and r["TR"] > r["S3"]
        ) else "Fail",
        axis=1
    )
    diag["Failed Signal"] = diag.apply(fail_reason, axis=1)

    st.dataframe(
        diag.sort_values("Status"),
        use_container_width=True
    )

    # -------------------------------------------------
    # 2D — Regime stability
    # -------------------------------------------------
    st.subheader("2️⃣ Regime Stability (Full History)")

    def pass_rate(country):
        tr = country_ts.set_index("date")[country]
        s1c = s1.set_index("date")[country]
        s2c = s2.set_index("date")[country]
        s3c = s3.set_index("date")[country]
        return ((tr > s1c) & (tr > s2c) & (tr > s3c)).mean() * 100

    stability = pd.DataFrame({
        "Pass Rate (%)": {c: pass_rate(c) for c in score.columns}
    }).sort_values("Pass Rate (%)")

    st.dataframe(
        stability.style.format({"Pass Rate (%)": "{:.1f}%"}),
        use_container_width=True
    )

    # -------------------------------------------------
    # 4G — Regime context
    # -------------------------------------------------
    st.subheader("3️⃣ Regime Context – Have we seen this before?")

    def breadth(dt):
        tr = country_ts.set_index("date").loc[dt]
        s1d = s1.set_index("date").loc[dt]
        s2d = s2.set_index("date").loc[dt]
        s3d = s3.set_index("date").loc[dt]
        return ((tr > s1d) & (tr > s2d) & (tr > s3d)).mean()

    breadth_series = pd.Series({d: breadth(d) for d in signal_dates})

    current_breadth = breadth(selected_date)
    percentile = (breadth_series <= current_breadth).mean() * 100

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Trend Breadth (%)", f"{current_breadth * 100:.1f}%")
    with col2:
        st.metric("Historical Percentile", f"{percentile:.1f}%")

    fig, ax = plt.subplots()
    ax.plot(breadth_series.index, breadth_series.values * 100)
    ax.axvline(selected_date, color="red", linestyle="--")
    ax.set_ylabel("% Passing Trend")
    ax.set_title("Trend Breadth Over Time")
    st.pyplot(fig)

    # -------------------------------------------------
    # I — IC readiness
    # -------------------------------------------------
    st.subheader("4️⃣ IC Readiness")

    st.write(
        "This page provides governance‑grade diagnostics:\n\n"
        "- Explicit reasons for each country passing or failing trend\n"
        "- Long‑run stability statistics by country\n"
        "- Regime context vs historical breadth\n\n"
        "All views are strictly aligned to Signal‑date holdings "
        "and use the Score tab as the full cross‑sectional universe."
    )
