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
# Helper functions (analytics)
# =====================================================

def to_long(df, value_name):
    return (
        df
        .melt(id_vars="date", var_name="country", value_name=value_name)
        .sort_values("date")
    )


def compute_forward_returns(ts_df, horizon=1):
    """
    Forward returns in PERCENT terms (e.g. 1.2 = +1.2%)
    """
    ts_long = to_long(ts_df, "level")
    ts_long["fwd_return_pct"] = (
        ts_long
        .groupby("country")["level"]
        .shift(-horizon) / ts_long["level"] - 1
    ) * 100
    return ts_long.dropna(subset=["fwd_return_pct"])


def score_long_format(score_df):
    return to_long(score_df, "score")


def trend_diagnostics(ts, s1, s2, s3):
    tr = to_long(ts, "tr")
    s1l = to_long(s1, "s1")
    s2l = to_long(s2, "s2")
    s3l = to_long(s3, "s3")

    df = (
        tr
        .merge(s1l, on=["date", "country"], how="left")
        .merge(s2l, on=["date", "country"], how="left")
        .merge(s3l, on=["date", "country"], how="left")
    )

    df["pass_trend"] = (
        (df["tr"] > df["s1"]) &
        (df["tr"] > df["s2"]) &
        (df["tr"] > df["s3"])
    ).fillna(False)

    df["failed_signal"] = df.apply(
        lambda r: (
            "S1" if r["tr"] <= r["s1"] else
            "S2" if r["tr"] <= r["s2"] else
            "S3" if r["tr"] <= r["s3"] else
            "Pass"
        ),
        axis=1
    )

    return df


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
    score_filter,
    score,
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

    st.write(f"As of {latest_date.date()}")

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

    ts, s1_, s2_, s3_, sc = map(sl, [country_ts, s1, s2, s3, score])

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
        ax.axhline(0, color="red", ls="--")
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        st.pyplot(fig)

# =====================================================
# SIGNAL SUMMARY PAGE
# =====================================================

if page == "Signal Summary":

    st.header("📊 Signal Summary (Signal-Date Aligned)")

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
# SIGNAL ANALYTICS PAGE
# =====================================================

if page == "Signal Analytics":

    st.header("🧪 Signal Analytics & Historical Context")

    score_long = score_long_format(score)
    fwd = compute_forward_returns(country_ts, 1)
    merged = score_long.merge(fwd, on=["date", "country"], how="inner")
    trend_hist = trend_diagnostics(country_ts, s1, s2, s3)

    signal_dates = signal["date"].drop_duplicates().sort_values()
    current_date = st.selectbox(
        "Select signal date",
        signal_dates,
        index=len(signal_dates) - 1,
        format_func=lambda d: d.strftime("%B %Y")
    )

    # ---- Extremeness (absolute scores)
    st.subheader("Score Extremeness (Absolute Levels)")

    cs = score_long[score_long["date"] == current_date]
    st.dataframe(
        cs.sort_values("score", ascending=False),
        use_container_width=True
    )

    # ---- Failure diagnostics
    st.subheader("Trend Failure Diagnostics")

    td = trend_hist[trend_hist["date"] == current_date]
    st.dataframe(
        td[["country", "tr", "s1", "s2", "s3", "pass_trend", "failed_signal"]]
        .sort_values("pass_trend"),
        use_container_width=True
    )

    # ---- Regime stability
    st.subheader("Regime Stability")

    stability = (
        trend_hist
        .groupby("country")["pass_trend"]
        .agg(pass_rate="mean", months_passing="sum", obs="count")
        .sort_values("pass_rate")
    )
    stability["pass_rate"] *= 100

    st.dataframe(
        stability.style.format({"pass_rate": "{:.1f}%"}),
        use_container_width=True
    )

    # ---- Forward returns at similar score levels
    st.subheader("Forward 1‑Month Returns at Similar Score Levels")

    c = st.selectbox("Select country", cs["country"].sort_values().unique())
    score_now = cs.loc[cs["country"] == c, "score"].iloc[0]

    lower = score_now * 0.9
    upper = score_now * 1.1

    bucket = merged[
        (merged["country"] == c) &
        (merged["score"].between(lower, upper))
    ]

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.hist(bucket["fwd_return_pct"], bins=20)
        ax.axvline(0, color="red", ls="--")
        ax.set_title("Forward 1‑Month Return Distribution")
        ax.set_xlabel("Return (%)")
        st.pyplot(fig)

    with col2:
        st.metric("Prob. Positive Return", f"{(bucket['fwd_return_pct'] > 0).mean():.1%}")
        st.metric("Median Return", f"{bucket['fwd_return_pct'].median():.2f}%")

    # ---- Cross‑sectional score → return relationship
    st.subheader("Score → Forward Return Relationship")

    merged["score_bucket"] = pd.qcut(
        merged["score"],
        10,
        labels=False,
        duplicates="drop"
    )

    dec = (
        merged
        .groupby("score_bucket")["fwd_return_pct"]
        .agg(mean="mean", median="median", hit=lambda x: (x > 0).mean())
    )
    dec["hit"] *= 100

    fig, ax = plt.subplots()
    ax.plot(dec.index, dec["mean"], marker="o")
    ax.set_title("Average Forward 1‑Month Return by Score Bucket")
    ax.set_xlabel("Score Bucket (low → high)")
    ax.set_ylabel("Return (%)")
    st.pyplot(fig)

    st.dataframe(
        dec.style.format(
            {
                "mean": "{:.2f}%",
                "median": "{:.2f}%",
                "hit": "{:.1f}%"
            }
        ),
        use_container_width=True
    )
