# EMD Signal Dashboard

Streamlit dashboard for visualising systematic EMD signal strategies.

## Inputs
- `country_index_ts.csv`: country total return indices
- `signal.csv`: monthly Top‑X country selections
- `signal_performance.csv`: pre‑computed strategy returns

## Philosophy
- Signals are computed externally (Excel)
- Python aggregates and visualises only
- No signal logic is re‑implemented

## Deployment
1. Push repo to GitHub
2. Connect to Streamlit Community Cloud
3. Set entry point: `app.py`
