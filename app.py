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
# Basic helpers (simple & explicit)
# =====================================================

def to_long(df, value_name):
    return df.melt(
        id_vars="date",
        var_name="country",
        value_name=value_name
    ).sort_values("date")


def forward_1m_returns(ts):
    """
    Forward 1M total return in PERCENT terms
    """
    ts_long = to_long(ts, "level")
    ts_long["fwd_1m_pct"] = (
        ts_long.groupby("country")["level"].shift(-1) / ts_long["level"] - 1
    ) * 100
    return ts_long.dropna(subset=["fwd_1m_pct"])


# =====================================================
# Streamlit setup
# =====================================================

st.set_page_config(page_title="Momentum Signal Dashboard", layout="wide")
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
    score_filter,  # kept but not used here
    score,         # SCORE tab (absolute levels)
) = cached_load(uploaded_file)


page = st.sidebar.radio(
    "Page",
    ["Performance", "Signals", "Signal Summary", "Signal Analytics"]
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
# SIGNAL SUMMARY PAGE (signal‑date aligned)
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
    summary = pd.DataFrame({"score": score_row})

    summary["tr"] = country_ts.set_index("date").loc[selected_date].reindex(summary.index)
    summary["s1"] = s1.set_index("date").loc[selected_date].reindex(summary.index)
    summary["s2"] = s2.set_index("date").loc[selected_date].reindex(summary.index)
    summary["s3"] = s3.set_index("date").loc[selected_date].reindex(summary.index)

    summary["pass_trend"] = (
        (summary["tr"] > summary["s1"]) &
        (summary["tr"] > summary["s2"]) &
        (summary["tr"] > summary["s3"])
    ).fillna(False)

    fails = summary[~summary["pass_trend"]].sort_values("score")
    passes = summary[summary["pass_trend"]].sort_values("score")

    plot_df = pd.concat([fails, passes])
    colours = ["red"] * len(fails) + ["tab:blue"] * len(passes)

    fig, ax = plt.subplots(figsize=(9, max(6, 0.28 * len(plot_df))))
    ax.barh(plot_df.index, plot_df["score"], color=colours, edgecolor="black", alpha=0.85)
    ax.set_title(f"Score vs Trend Confirmation — {selected_date.strftime('%B %Y')}")
    ax.set_xlabel("Score")
    ax.grid(axis="x")
    st.pyplot(fig)


# =====================================================
# SIGNAL ANALYTICS PAGE (clean & robust)
# =====================================================

if page == "Signal Analytics":

    st.header("🧪 Signal Analytics (Absolute Scores & Forward Returns)")

    score_long = to_long(score, "score")
    fwd = forward_1m_returns(country_ts)

    merged = score_long.merge(
        fwd,
        on=["date", "country"],
        how="inner"
    )

    signal_dates = signal["date"].drop_duplicates().sort_values()

    current_date = st.selectbox(
        "Select signal date",
        signal_dates,
        index=len(signal_dates) - 1,
        format_func=lambda d: d.strftime("%B %Y")
    )

    st.subheader("1️⃣ Current Absolute Score Levels")

    current_scores = score_long[score_long["date"] == current_date]
    st.dataframe(
        current_scores.sort_values("score", ascending=False),
        use_container_width=True
    )

    st.subheader("2️⃣ Forward 1‑Month Returns at Similar Score Levels")

    country = st.selectbox(
        "Select country",
        current_scores["country"].sort_values().unique()
    )

    current_score = current_scores.loc[
        current_scores["country"] == country, "score"
    ].iloc[0]

    # Simple, stable conditioning band
    lower = current_score * 0.9
    upper = current_score * 1.1

    bucket = merged[
        (merged["country"] == country) &
        (merged["score"].between(lower, upper))
    ]

    st.caption(
        f"Conditioning on score ≈ {current_score:.2f} (±10%)"
    )

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.hist(bucket["fwd_1m_pct"], bins=20)
        ax.axvline(0, color="red", linestyle="--")
        ax.set_xlabel("Forward 1‑Month Return (%)")
        ax.set_title("Distribution")
        st.pyplot(fig)

    with col2:
        st.metric(
            "Probability of Positive Return",
            f"{(bucket['fwd_1m_pct'] > 0).mean():.1%}"
        )
        st.metric(
            "Median Forward Return",
            f"{bucket['fwd_1m_pct'].median():.2f}%"
        )

    st.subheader("3️⃣ Score → Forward Return Sanity Check")

    merged["score_bucket"] = pd.qcut(
        merged["score"],
        8,
        duplicates="drop"
    )

    bucket_stats = (
        merged
        .groupby("score_bucket")["fwd_1m_pct"]
        .agg(["mean", "median", lambda x: (x > 0).mean() * 100])
        .rename(columns={"<lambda_0>": "hit_rate"})
    )

    fig, ax = plt.subplots()
    ax.plot(bucket_stats.index.astype(str), bucket_stats["mean"], marker="o")
    ax.set_ylabel("Avg Forward 1‑Month Return (%)")
    ax.set_title("Score Bucket vs Forward Returns")
    st.pyplot(fig)

    st.dataframe(
        bucket_stats.style.format(
            {
                "mean": "{:.2f}%",
                "median": "{:.2f}%",
                "hit_rate": "{:.1f}%"
            }
        ),
        use_container_width=True
    )
