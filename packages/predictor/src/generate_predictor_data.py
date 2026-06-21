import os
import json
import random
from datetime import datetime, timedelta

# Create directories
os.makedirs("data/predictor/constituents", exist_ok=True)
os.makedirs("data/predictor/prices", exist_ok=True)
os.makedirs("data/predictor/fundamentals", exist_ok=True)

# Universe of 20 tickers
TICKERS = [
    "ITC", "HINDUNILVR", "BRITANNIA", "NESTLEIND",
    "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK",
    "TCS", "INFY", "WIPRO", "HCLTECH",
    "RELIANCE", "ONGC", "POWERGRID", "NTPC",
    "TATAMOTORS", "M&M", "MARUTI", "EICHERMOT"
]

REBALANCE_DATES = [
    "2023-05-30",
    "2023-11-30",
    "2024-05-30",
    "2024-11-30",
    "2025-05-30",
    "2025-11-30",
    "2026-05-30"
]

random.seed(42)

def generate_historical_prices():
    """Generates 3 years (~750 trading days) of daily OHLCV prices for the 20 tickers."""
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2026, 6, 19)
    delta = end_date - start_date
    days_count = delta.days
    
    # Define price baselines
    baselines = {
        "ITC": 300.0, "HINDUNILVR": 2000.0, "BRITANNIA": 4000.0, "NESTLEIND": 1800.0,
        "HDFCBANK": 1400.0, "ICICIBANK": 800.0, "SBIN": 500.0, "KOTAKBANK": 1600.0,
        "TCS": 3000.0, "INFY": 1200.0, "WIPRO": 380.0, "HCLTECH": 1000.0,
        "RELIANCE": 2200.0, "ONGC": 150.0, "POWERGRID": 200.0, "NTPC": 180.0,
        "TATAMOTORS": 400.0, "M&M": 1200.0, "MARUTI": 8000.0, "EICHERMOT": 3000.0
    }
    
    # Define trends (positive drift = strong momentum, negative drift = underperforming)
    drifts = {
        "RELIANCE": 0.0006, "TCS": 0.0005, "ITC": 0.0004, "TATAMOTORS": 0.0008, 
        "HDFCBANK": 0.0004, "ICICIBANK": 0.0007, "M&M": 0.0006, "BRITANNIA": 0.0005,
        "ONGC": 0.0003, "POWERGRID": 0.0002, "SBIN": 0.0001, "KOTAKBANK": 0.0002,
        "NESTLEIND": 0.0001, "HINDUNILVR": 0.0002, "NTPC": 0.0003, "EICHERMOT": 0.0002,
        "INFY": -0.0001, "WIPRO": -0.0004, "HCLTECH": 0.0001, "MARUTI": 0.0002
    }
    
    for ticker in TICKERS:
        price = baselines[ticker]
        drift = drifts[ticker]
        vol = 0.018 # volatility
        
        history = []
        
        for i in range(days_count):
            curr_date = start_date + timedelta(days=i)
            # Skip weekends
            if curr_date.weekday() >= 5:
                continue
                
            date_str = curr_date.strftime("%Y-%m-%d")
            
            ret = drift + vol * random.normalvariate(0, 1)
            prev_close = price
            price = prev_close * (1 + ret)
            if price < 5:
                price = 5.0
                
            daily_range = price * 0.02 * abs(random.normalvariate(0, 1))
            open_p = prev_close
            close_p = price
            high_p = max(open_p, close_p) + daily_range * 0.4
            low_p = min(open_p, close_p) - daily_range * 0.4
            
            history.append({
                "date": date_str,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": int(random.uniform(500000, 5000000))
            })
            
        # Write ticker prices file
        with open(f"data/predictor/prices/{ticker}.json", "w") as f:
            json.dump(history, f, indent=2)

def generate_historical_constituents():
    """Generates index constituents logs for Nifty Momentum 50 (represented by top 8 stocks here)."""
    # Create constituents list per rebalance date
    constituents_data = {}
    
    # We will pick 8 index constituents for each date based on their momentum trends
    # Bullish stocks are highly likely to be in the index, bearish stocks likely to drop out
    for date_str in REBALANCE_DATES:
        # Determine index constituents for this date
        # In May 2023, start with a base
        if date_str == "2023-05-30":
            active = ["RELIANCE", "TCS", "ITC", "HDFCBANK", "ICICIBANK", "BRITANNIA", "TCS", "HINDUNILVR", "TATAMOTORS"]
        elif date_str == "2023-11-30":
            active = ["RELIANCE", "TCS", "ITC", "HDFCBANK", "ICICIBANK", "BRITANNIA", "TATAMOTORS", "M&M"]
        elif date_str == "2024-05-30":
            active = ["RELIANCE", "ITC", "HDFCBANK", "ICICIBANK", "BRITANNIA", "TATAMOTORS", "M&M", "ONGC"]
        elif date_str == "2024-11-30":
            active = ["RELIANCE", "ICICIBANK", "BRITANNIA", "TATAMOTORS", "M&M", "ONGC", "HINDUNILVR", "NTPC"]
        elif date_str == "2025-05-30":
            active = ["RELIANCE", "ICICIBANK", "BRITANNIA", "TATAMOTORS", "M&M", "ONGC", "HINDUNILVR", "NTPC"]
        else: # 2025-11-30 and 2026-05-30
            active = ["ICICIBANK", "RELIANCE", "BRITANNIA", "ONGC", "M&M", "HINDUNILVR", "NTPC", "TATAMOTORS"]
            
        # Clean duplicates and list them
        active = list(set(active))
        constituents_data[date_str] = active
        
    with open("data/predictor/constituents/nifty_500_momentum_50.json", "w") as f:
        json.dump(constituents_data, f, indent=2)

def generate_fundamentals_history():
    """Generates quarterly fundamentals parameters per stock."""
    fundamentals_data = {}
    for ticker in TICKERS:
        fundamentals_data[ticker] = {
            "roce": round(random.uniform(15, 38), 1),
            "roe": round(random.uniform(12, 32), 1),
            "debt_to_equity": round(random.uniform(0.01, 0.8), 2)
        }
        # Add flags specific to some tickers
        if ticker in ["SBIN", "POWERGRID"]:
            fundamentals_data[ticker]["debt_to_equity"] = round(random.uniform(1.6, 2.2), 2)
            
    with open("data/predictor/fundamentals/fundamentals.json", "w") as f:
        json.dump(fundamentals_data, f, indent=2)

if __name__ == "__main__":
    generate_historical_prices()
    generate_historical_constituents()
    generate_fundamentals_history()
    print("Generated historical simulation datasets successfully under data/predictor/.")
