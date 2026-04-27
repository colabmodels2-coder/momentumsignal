import pandas as pd

def load_all_data():
    country_ts = pd.read_csv(
        "data/country_index_ts.csv",
        parse_dates=["date"]
    )

    signal = pd.read_csv(
        "data/signal.csv",
        parse_dates=["date"]
    )

    signal_perf = pd.read_csv(
        "data/signal_performance.csv",
        parse_dates=["date"]
    )

    return country_ts, signal, signal_perf
