import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def load_all_data():
    uploaded_file = st.file_uploader(
        "Upload Momentum Signal Excel file",
        type=["xlsx"]
    )

    if uploaded_file is None:
        st.stop()

    # ---------------------------
    # Country Index TS
    # ---------------------------
    country_ts = pd.read_excel(
        uploaded_file,
        sheet_name="Country Index TS",
        engine="openpyxl"
    ).rename(columns={"Dates": "date"})

    country_ts["date"] = pd.to_datetime(country_ts["date"])

    # ---------------------------
    # Signal (Top-X selections)
    # ---------------------------
    signal = pd.read_excel(
        uploaded_file,
        sheet_name="Signal",
        engine="openpyxl"
    ).rename(columns={
        "Date": "date",
        "Rank": "rank",
        "Country": "country"
    })

    signal["date"] = pd.to_datetime(signal["date"])

    # ---------------------------
    # Signal Performance (WIDE → LONG)
    # Columns you described:
    # Dates, Top1 ... Top5 (+ cumulative / drawdown ignored)
    # ---------------------------
    signal_perf_wide = pd.read_excel(
        uploaded_file,
        sheet_name="Signal Performance",
        engine="openpyxl"
    ).rename(columns={"Dates": "date"})

    signal_perf_wide["date"] = pd.to_datetime(signal_perf_wide["date"])

    strategy_cols = ["Top1", "Top2", "Top3", "Top4", "Top5"]

    missing = [c for c in strategy_cols if c not in signal_perf_wide.columns]
    if missing:
        st.error(f"Missing strategy columns in Signal Performance: {missing}")
        st.stop()

    signal_perf = signal_perf_wide.melt(
        id_vars="date",
        value_vars=strategy_cols,
        var_name="strategy",
        value_name="return"
    ).dropna(subset=["return"])

    return country_ts, signal, signal_perf
