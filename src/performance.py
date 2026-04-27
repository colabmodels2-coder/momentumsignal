import pandas as pd
import numpy as np

def compute_cumulative_returns(perf_df):
    df = perf_df.sort_values("date").copy()
    df["cum_return"] = (1 + df["return"]).cumprod()
    return df

def compute_drawdown(cum_df):
    peak = cum_df["cum_return"].cummax()
    return cum_df["cum_return"] / peak - 1

def rolling_12m_returns(perf_df, window=12):
    return (
        perf_df
        .sort_values("date")
        .set_index("date")["return"]
        .rolling(window)
        .apply(lambda x: (1 + x).prod() - 1)
        .dropna()
    )
