import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Load tickers configuration
TICKERS = [
    "ITC", "HINDUNILVR", "BRITANNIA", "NESTLEIND",
    "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK",
    "TCS", "INFY", "WIPRO", "HCLTECH",
    "RELIANCE", "ONGC", "POWERGRID", "NTPC",
    "TATAMOTORS", "M&M", "MARUTI", "EICHERMOT"
]

CAPS = {
    "ITC": 584200, "HINDUNILVR": 575000, "BRITANNIA": 118000, "NESTLEIND": 241000,
    "HDFCBANK": 1230000, "ICICIBANK": 780000, "SBIN": 730000, "KOTAKBANK": 348000,
    "TCS": 1410000, "INFY": 614000, "WIPRO": 225000, "HCLTECH": 358000,
    "RELIANCE": 1995000, "ONGC": 340000, "POWERGRID": 298000, "NTPC": 349000,
    "TATAMOTORS": 358000, "M&M": 348000, "MARUTI": 380000, "EICHERMOT": 129000
}

def load_ticker_prices(ticker: str) -> pd.DataFrame:
    path = f"data/predictor/prices/{ticker}.json"
    with open(path, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df

def load_constituents() -> Dict[str, List[str]]:
    with open("data/predictor/constituents/nifty_500_momentum_50.json", "r") as f:
        return json.load(f)

def load_fundamentals() -> Dict[str, Dict[str, float]]:
    with open("data/predictor/fundamentals/fundamentals.json", "r") as f:
        return json.load(f)

def compute_features_for_date(target_date_str: str) -> pd.DataFrame:
    """Computes feature vectors for all 20 tickers at a given historical rebalance date."""
    target_date = pd.to_datetime(target_date_str)
    
    # Load all ticker prices
    price_dfs = {}
    for t in TICKERS:
        price_dfs[t] = load_ticker_prices(t)
        
    # Load constituents and fundamentals
    constituents = load_constituents()
    fundamentals = load_fundamentals()
    
    # Resolve index dates to check current/prev status
    sorted_dates = sorted(list(constituents.keys()))
    current_idx_list = constituents.get(target_date_str, [])
    
    # Resolve previous index date to check was_added_prev
    prev_date_str = None
    if target_date_str in sorted_dates:
        target_idx = sorted_dates.index(target_date_str)
        if target_idx > 0:
            prev_date_str = sorted_dates[target_idx - 1]
            
    prev_idx_list = constituents.get(prev_date_str, []) if prev_date_str else []

    # Calculate returns for each stock to compute benchmark averages
    rets_12m = {}
    rets_6m = {}
    rets_3m = {}
    
    for t in TICKERS:
        df = price_dfs[t]
        # Filter prices up to target_date
        df_hist = df[:target_date]
        if len(df_hist) < 250:
            continue
            
        closes = df_hist["close"].values
        # Returns over 250 trading days (~12m), 125 days (~6m), 63 days (~3m)
        rets_12m[t] = (closes[-1] - closes[-250]) / closes[-250]
        rets_6m[t] = (closes[-1] - closes[-125]) / closes[-125]
        rets_3m[t] = (closes[-1] - closes[-63]) / closes[-63]
        
    # Calculate universe benchmark averages
    avg_ret_12m = np.mean(list(rets_12m.values()))
    avg_ret_6m = np.mean(list(rets_6m.values()))
    avg_ret_3m = np.mean(list(rets_3m.values()))

    records = []
    
    for t in TICKERS:
        df = price_dfs[t]
        df_hist = df[:target_date]
        if len(df_hist) < 250:
            continue
            
        closes = df_hist["close"].values
        volumes = df_hist["volume"].values
        
        # 1. Relative Strength factors
        rs_12m = rets_12m[t] - avg_ret_12m
        rs_6m = rets_6m[t] - avg_ret_6m
        rs_3m = rets_3m[t] - avg_ret_3m
        
        # Methodology approximation: 50% of 12m RS + 30% of 6m RS + 20% of 3m RS
        rs_momentum_score = (rs_12m * 0.5) + (rs_6m * 0.3) + (rs_3m * 0.2)
        
        # 2. Volume ratio
        vol_3m = np.mean(volumes[-63:])
        vol_6m = np.mean(volumes[-125:])
        volume_ratio_3m = vol_3m / vol_6m if vol_6m > 0 else 1.0
        
        # 3. Distance from 200 EMA
        # Compute 200 EMA
        df_hist_copy = df_hist.copy()
        df_hist_copy["ema_200"] = df_hist_copy["close"].ewm(span=200, adjust=False).mean()
        ema200 = df_hist_copy["ema_200"].iloc[-1]
        ema_200_distance_pct = ((closes[-1] - ema200) / ema200) * 100
        
        # 4. Market Cap Rank at rebalance date
        # Cap grows proportionally to price return since start baseline
        price_ret = (closes[-1] - closes[0]) / closes[0]
        curr_cap = CAPS[t] * (1 + price_ret)
        
        # 5. Fundamentals
        fund = fundamentals.get(t, {"roe": 15.0, "roce": 18.0, "debt_to_equity": 0.5})
        
        # 6. Target label (Inclusion in the target rebalance date index)
        # Check if the stock is in current index list
        is_constituent = t in current_idx_list
        was_added_prev = t in prev_idx_list
        
        records.append({
            "ticker": t,
            "rebalance_date": target_date_str,
            "rs_12m": round(rs_12m * 100, 2), # convert to %
            "rs_6m": round(rs_6m * 100, 2),
            "rs_3m": round(rs_3m * 100, 2),
            "rs_momentum_score": round(rs_momentum_score * 100, 2),
            "volume_ratio_3m": round(volume_ratio_3m, 3),
            "ema_200_distance_pct": round(ema_200_distance_pct, 2),
            "roce": fund["roce"],
            "roe": fund["roe"],
            "debt_to_equity": fund["debt_to_equity"],
            "curr_cap": curr_cap, # helper to calculate rank later
            "current_constituent": 1 if is_constituent else 0,
            "was_added_prev": 1 if was_added_prev else 0,
        })
        
    df_features = pd.DataFrame(records)
    if df_features.empty:
        return df_features
        
    # Calculate market cap rank across the universe
    df_features["market_cap_rank"] = df_features["curr_cap"].rank(ascending=False).astype(int)
    # Drop helper column
    df_features.drop(columns=["curr_cap"], inplace=True)
    
    return df_features

def build_training_dataset(dates: List[str]) -> pd.DataFrame:
    """Combines features across multiple rebalance dates to create a unified training set."""
    dfs = []
    for d in dates:
        df_d = compute_features_for_date(d)
        if not df_d.empty:
            dfs.append(df_d)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
