import matplotlib.pyplot as plt
from src.performance import compute_drawdown, rolling_12m_returns

def plot_cumulative_returns(cum_df, strategy):
    fig, ax = plt.subplots()
    ax.plot(cum_df["date"], cum_df["cum_return"])
    ax.set_title(f"Cumulative Return – {strategy}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of $1")
    return fig

def plot_drawdowns(cum_df):
    drawdown = compute_drawdown(cum_df)
    fig, ax = plt.subplots()
    ax.fill_between(cum_df["date"], drawdown, 0)
    ax.set_title("Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    return fig

def plot_rolling_returns(perf_df, window=12):
    roll = rolling_12m_returns(perf_df, window)
    fig, ax = plt.subplots()
    ax.plot(roll.index, roll.values)
    ax.set_title(f"Rolling {window}‑Month Returns")
    ax.set_xlabel("Date")
    ax.set_ylabel("Return")
    return fig

def plot_return_distribution(perf_df, window=12):
    roll = rolling_12m_returns(perf_df, window)
    fig, ax = plt.subplots()
    ax.hist(roll.values, bins=30)
    ax.set_title(f"Distribution of Rolling {window}‑Month Returns")
    ax.set_xlabel("Return")
    ax.set_ylabel("Frequency")
    return fig
