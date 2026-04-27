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

    # =========================
    # Country Index TS
    # =========================
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

    # =========================
    # Signal (rank matrix)
    # =========================
    signal_wide = pd.read_excel(
        uploaded_file,
        sheet_name="Signal",
        engine="openpyxl"
    )

    signal_wide.columns = signal_wide.columns.map(str)

    required_signal_cols = {"Dates", "1", "2", "3", "4", "5"}
    if not required_signal_cols.issubset(signal_wide.columns):
        st.error("Signal sheet must contain columns: Dates, 1–5")
        st.stop()

    signal_wide = signal_wide.rename(columns={"Dates": "date"})
    signal_wide["date"] = pd.to_datetime(signal_wide["date"])

    signal = signal_wide.melt(
        id_vars="date",
        value_vars=["1", "2", "3", "4", "5"],
        var_name="rank",
        value_name="country"
    )

    signal["rank"] = signal["rank"].astype(int)
    signal = signal.dropna(subset=["country"])

    # =========================
    # Signal Performance
    # =========================
    signal_perf_wide = pd.read_excel(
        uploaded_file,
        sheet_name="Signal Performance",
        engine="openpyxl"
    )

    signal_perf_wide.columns = signal_perf_wide.columns.map(str)

    if "Dates" not in signal_perf_wide.columns:
        st.error("Signal Performance must contain a 'Dates' column.")
        st.stop()

    signal_perf_wide = signal_perf_wide.rename(columns={"Dates": "date"})
    signal_perf_wide["date"] = pd.to_datetime(signal_perf_wide["date"])

    strategy_cols = ["Top1", "Top2", "Top3", "Top4", "Top5"]

    signal_perf = signal_perf_wide.melt(
        id_vars="date",
        value_vars=strategy_cols,
        var_name="strategy",
        value_name="return"
    ).dropna(subset=["return"])

    # =========================
    # S1 / S2 / S3 / Score Filter
    # =========================
    def load_signal_sheet(name):
        df = pd.read_excel(
            uploaded_file,
            sheet_name=name,
            engine="openpyxl"
        )
        df = df.rename(columns={"Dates": "date"})
        df["date"] = pd.to_datetime(df["date"])
        return df

    s1 = load_signal_sheet("S1")
    s2 = load_signal_sheet("S2")
    s3 = load_signal_sheet("S3")
    score_filter = load_signal_sheet("Score Filter")

    return country_ts, signal, signal_perf, s1, s2, s3, score_filter
