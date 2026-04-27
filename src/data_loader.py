import pandas as pd

EXCEL_PATH = "data/emd_signals.xlsx"

def load_all_data():
    # Country total return indices (wide format, same as Excel)
    country_ts = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Country Index TS",
        parse_dates=["Date"]
    ).rename(columns={"Date": "date"})

    # Signal selections
    signal = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Signal",
        parse_dates=["Date"]
    ).rename(columns={
        "Date": "date",
        "Rank": "rank",
        "Country": "country"
    })

    # Strategy performance
    signal_perf = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Signal Performance",
        parse_dates=["Date"]
    ).rename(columns={
        "Date": "date",
        "Strategy": "strategy",
        "Return": "return"
    })

    return country_ts, signal, signal_perf
