import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def load_all_data():
    """
    Loads all data from a single uploaded Excel file.

    Expected Excel structure:

    1. Country Index TS
       - Column: Dates
       - Other columns: country total return indices (wide)

    2. Signal (RANK MATRIX)
       - Columns: Dates, 1, 2, 3, 4, 5
       - Values under 1–5 are country names

    3. Signal Performance (WIDE)
       - Columns: Dates, Top1, Top2, Top3, Top4, Top5
    """

    uploaded_file = st.file_uploader(
        "Upload Momentum Signal Excel file",
        type=["xlsx"]
    )

    if uploaded_file is None:
        st.stop()

    # ====================================================
    # Country Index TS
    # ====================================================
    country_ts = pd.read_excel(
        uploaded_file,
        sheet_name="Country Index TS",
        engine="openpyxl"
    )

    if "Dates" not in country_ts.columns:
        st.error("Country Index TS must contain a 'Dates' column.")
        st.stop()

    country_ts = country_ts.rename(columns={"Dates": "date"})
    country_ts["date"] = pd.to_datetime(country_ts["date"])

    # ====================================================
    # Signal (RANK MATRIX → LONG FORMAT)
    # ====================================================
    signal_wide = pd.read_excel(
        uploaded_file,
        sheet_name="Signal",
        engine="openpyxl"
    )

    required_signal_cols = {"Dates", "1", "2", "3", "4", "5"}
    missing_signal = required_signal_cols - set(signal_wide.columns.astype(str))

    if missing_signal:
        st.error(f"Signal sheet missing required columns: {missing_signal}")
        st.stop()

    signal_wide = signal_wide.rename(columns={"Dates": "date"})
    signal_wide["date"] = pd.to_datetime(signal_wide["date"])

    # Reshape ranks into (date, rank, country)
    signal = signal_wide.melt(
        id_vars="date",
        value_vars=["1", "2", "3", "4", "5"],
        var_name="rank",
        value_name="country"
    )

    signal["rank"] = signal["rank"].astype(int)
    signal = signal.dropna(subset=["country"])

    # ====================================================
    # Signal Performance (WIDE → LONG)
    # ====================================================
    signal_perf_wide = pd.read_excel(
        uploaded_file,
        sheet_name="Signal Performance",
        engine="openpyxl"
    )

    if "Dates" not in signal_perf_wide.columns:
        st.error("Signal Performance must contain a 'Dates' column.")
        st.stop()

    signal_perf_wide = signal_perf_wide.rename(columns={"Dates": "date"})
    signal_perf_wide["date"] = pd.to_datetime(signal_perf_wide["date"])

    strategy_cols = ["Top1", "Top2", "Top3", "Top4", "Top5"]
    missing_strategies = [c for c in strategy_cols if c not in signal_perf_wide.columns]

    if missing_strategies:
        st.error(f"Signal Performance missing strategy columns: {missing_strategies}")
        st.stop()

    signal_perf = signal_perf_wide.melt(
        id_vars="date",
        value_vars=strategy_cols,
        var_name="strategy",
        value_name="return"
    )

    signal_perf = signal_perf.dropna(subset=["return"])

    return country_ts, signal, signal_perf
