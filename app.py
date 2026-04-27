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
# File uploader (NOT cached)
# ============================
uploaded_file = st.file_uploader(
    "Upload Momentum Signal Excel file",
    type=["xlsx"]
)

if uploaded_file is None:
    st.stop()

# ============================
# Cached data load
# ============================
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
# PERFORMANCE PAGE
# =====================================================
if page == "Performance":

    st.sidebar.header("Controls")

    strategy_options = sorted(signal_perf["strategy"].unique())
    default_strategy = "Top5" if "Top5" in strategy_options else strategy_options[0]

    strategy = st.sidebar.selectbox(
        "Strategy",
        options=strategy_options,
        index=strategy_options.index(default_strategy)
    )

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
# SIGNALS PAGE (PER‑COUNTRY OVERSIGHT)
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
        ax.plot(sc["date"], sc[country], color="black", lw=2)
        ax.axhline(0, color="red", ls="--")
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        st.pyplot(fig)

# =====================================================
# SIGNAL SUMMARY PAGE (CORRECT AS-OF TREND TEST)
# =====================================================
if page == "Signal Summary":

    st.header("📊 Signal Summary – Cross‑Section")

    # -----------------------------
    # Date selector (monthly)
    # -----------------------------
    available_dates = (
        score_filter["date"]
        .dropna()
        .sort_values()
        .unique()
    )

    selected_date = st.selectbox(
        "Select signal date",
        options=available_dates,
        index=len(available_dates) - 1,
        format_func=lambda d: pd.to_datetime(d).strftime("%Y-%m")
    )

    # -----------------------------
    # Helper: wide → long
    # -----------------------------
    def to_long(df, name):
        return (
            df
            .melt(id_vars="date", var_name="country", value_name=name)
            .sort_values("date")
        )

    tr_long = to_long(country_ts, "tr")
    s1_long = to_long(s1, "s1")
    s2_long = to_long(s2, "s2")
    s3_long = to_long(s3, "s3")
    score_long = to_long(score_filter, "score")

    # -----------------------------
    # Base universe = SCORE
    # -----------------------------
    base = score_long[score_long["date"] == selected_date].copy()

    # -----------------------------
    # AS-OF alignment (critical)
    # -----------------------------
    base = pd.merge_asof(
        base.sort_values("date"),
        tr_long.sort_values("date"),
        on="date",
        by="country",
        direction="backward"
    )
    base = pd.merge_asof(base, s1_long, on="date", by="country", direction="backward")
    base = pd.merge_asof(base, s2_long, on="date", by="country", direction="backward")
    base = pd.merge_asof(base, s3_long, on="date", by="country", direction="backward")

    # -----------------------------
    # Correct trend rule
    # FAIL if TR <= any MA or missing
    # -----------------------------
    base["pass_trend"] = (
        (base["tr"] > base["s1"]) &
        (base["tr"] > base["s2"]) &
        (base["tr"] > base["s3"])
    ).fillna(False)

    # -----------------------------
    # Sort + colour
    # -----------------------------
    fails = base[~base["pass_trend"]].sort_values("score")
    passes = base[base["pass_trend"]].sort_values("score")
    plot_df = pd.concat([fails, passes])

    colours = (
        ["#d62728"] * len(fails) +   # red = fail trend
        ["#1f77b4"] * len(passes)    # blue = pass trend
    )

    # -----------------------------
    # Plot
    # -----------------------------
    fig, ax = plt.subplots(figsize=(9, max(6, len(plot_df) * 0.28)))

    ax.barh(
        plot_df["country"],
        plot_df["score"],
        color=colours,
        edgecolor="black",
        alpha=0.85
    )

    ax.set_title(
        f"Score Filter with Trend Confirmation – "
        f"{pd.to_datetime(selected_date).strftime('%Y-%m')}"
    )
    ax.set_xlabel("Score")
    ax.set_ylabel("Country")
    ax.grid(axis="x", alpha=0.4)

    import matplotlib.patches as mpatches
    legend_handles = [
        mpatches.Patch(color="#1f77b4", label="TR > S1, S2, S3 (Pass)"),
        mpatches.Patch(color="#d62728", label="TR ≤ one or more signals (Fail)")
    ]
    ax.legend(handles=legend_handles, loc="lower right")

    st.pyplot(fig)
