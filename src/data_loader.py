import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def load_all_data():
    """
    Loads all data from a single uploaded Excel file.

    Expected sheets and structure:

    1. Country Index TS
       - Date column: 'Dates'
       - Other columns: country total return indices (wide)

    2. Signal
       - Columns: 'Dates', 'Rank', 'Country'

    3. Signal Performance (wide)
       - Date column: 'Dates'
       - Strategy return columns: Top1, Top2, Top3, Top4, Top5
       - Other columns (cumulative, drawdown, etc.) are ignored
    """

    uploaded_file = st.file_uploader(
        "Upload Momentum Signal Excel file",
        type=["xlsx"]
    )

    if uploaded_file is None:
        st.stop()

    # =========================
    # Country Index TS
    # =========================
    country_ts = pd.read_excel(
        uploaded_file,
        sheet_name="Country Index TS",
        engine="openpyxl"
    )

    if "Dates" not in country_ts.columns:
        st.error("Country Index TS sheet must contain a 'Dates' column.")
        st.stop()

    country_ts = country_ts.rename(columns={"Dates": "date"})
    country_ts["date"] = pd.to_datetime(country_ts["date"])

    # =========================
    # Signal (Top-X selections)
    # =========================
    signal = pd.read_excel(
        uploaded_file,
        sheet_name="Signal",
        engine="openpyxl"
    )

    required_signal_cols = {"Dates", "Rank", "Country"}
    missing_signal = required_signal_cols - set(signal.columns)

    if missing_signal:
        st.error(f"Signal sheet missing required columns: {missing_signal}")
        st.stop()

    signal = signal.rename(columns={
        "Dates": "date",
        "Rank": "rank",
        "Country": "country"
    })

    signal["date"] = pd.to_datetime(signal["date"])
    signal["rank"] = signal["rank"].astype(int)

    # =========================
    # Signal Performance (WIDE → LONG)
    # =========================
    signal_perf_wide = pd.read_excel(
        uploaded_file,
        sheet_name="Signal Performance",
        engine="openpyxl"
    )

    if "Dates" not in signal_perf_wide.columns:
        st.error("Signal Performance sheet must contain a 'Dates' column.")
        st.stop()

    signal_perf_wide = signal_perf_wide.rename(columns={"Dates": "date"})
    signal_perf_wide["date"] = pd.to_datetime(signal_perf_wide["date"])

    strategy_cols = ["Top1", "Top2", "Top3", "Top4", "Top5"]
    missing_strategies = [c for c in strategy_cols if c not in signal_perf_wide.columns]

    if missing_strategies:
        st.error(
            f"Signal Performance sheet missing strategy return columns: "
            f"{missing_strategies}"
        )
        st.stop()

    signal_perf = signal_perf_wide.melt(
        id_vars="date",
        value_vars=strategy_cols,
        var_name="strategy",
        value_name="return"
    )

    signal_perf = signal_perf.dropna(subset=["return"])

    # =========================
    # Final sanity checks
    # =========================
    if signal_perf.empty:
        st.error("Signal Performance returned no data after reshaping.")
        st.stop()

    return country_ts, signal, signal_perf
