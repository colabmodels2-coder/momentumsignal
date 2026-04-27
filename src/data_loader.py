import pandas as pd

def load_all_data(uploaded_file):
    """
    Load and parse all Excel sheets.
    This function contains NO Streamlit widgets and is safe to cache.
    """

    # =========================
    # Country Index TS
    # =========================
    country_ts = pd.read_excel(
        uploaded_file,
        sheet_name="Country Index TS",
        engine="openpyxl"
    ).rename(columns={"Dates": "date"})
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
    signal_wide = signal_wide.rename(columns={"Dates": "date"})
    signal_wide["date"] = pd.to_datetime(signal_wide["date"])

    signal = signal_wide.melt(
        id_vars="date",
        value_vars=["1", "2", "3", "4", "5"],
        var_name="rank",
        value_name="country"
    ).dropna(subset=["country"])
    signal["rank"] = signal["rank"].astype(int)

    # =========================
    # Signal Performance
    # =========================
    signal_perf = pd.read_excel(
        uploaded_file,
        sheet_name="Signal Performance",
        engine="openpyxl"
    )
    signal_perf.columns = signal_perf.columns.map(str)
    signal_perf = signal_perf.rename(columns={"Dates": "date"})
    signal_perf["date"] = pd.to_datetime(signal_perf["date"])

    signal_perf = signal_perf.melt(
        id_vars="date",
        value_vars=["Top1", "Top2", "Top3", "Top4", "Top5"],
        var_name="strategy",
        value_name="return"
    ).dropna(subset=["return"])

    # =========================
    # Helper for signal sheets
    # =========================
    def load_signal_sheet(name):
        df = pd.read_excel(
            uploaded_file,
            sheet_name=name,
            engine="openpyxl"
        ).rename(columns={"Dates": "date"})
        df["date"] = pd.to_datetime(df["date"])
        return df

    # =========================
    # S1 / S2 / S3 / Score Filter
    # =========================
    s1 = load_signal_sheet("S1")
    s2 = load_signal_sheet("S2")
    s3 = load_signal_sheet("S3")
    score_filter = load_signal_sheet("Score Filter")

    # =========================
    # ✅ SCORE TAB (THIS WAS MISSING)
    # =========================
    score = pd.read_excel(
        uploaded_file,
        sheet_name="Score",
        engine="openpyxl"
    ).rename(columns={"Dates": "date"})
    score["date"] = pd.to_datetime(score["date"])

    # =========================
    # ✅ RETURN ORDER MUST MATCH app.py
    # =========================
    return (
        country_ts,
        signal,
        signal_perf,
        s1,
        s2,
        s3,
        score_filter,
        score,
    )
