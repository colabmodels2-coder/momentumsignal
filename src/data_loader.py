import pandas as pd
import streamlit as st

def load_all_data():
    uploaded_file = st.file_uploader(
        "Upload EMD signal Excel file",
        type=["xlsx"]
    )

    if uploaded_file is None:
        st.stop()

    country_ts = pd.read_excel(
        uploaded_file,
        sheet_name="Country Index TS",
        parse_dates=["Date"]
    ).rename(columns={"Date": "date"})

    signal = pd.read_excel(
        uploaded_file,
        sheet_name="Signal",
        parse_dates=["Date"]
    ).rename(columns={
        "Date": "date",
        "Rank": "rank",
        "Country": "country"
    })

    signal_perf = pd.read_excel(
        uploaded_file,
        sheet_name="Signal Performance",
        parse_dates=["Date"]
    ).rename(columns={
        "Date": "date",
        "Strategy": "strategy",
        "Return": "return"
    })

    return country_ts, signal, signal_perf
