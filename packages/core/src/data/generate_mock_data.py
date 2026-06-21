import json
import os
import random
from datetime import datetime, timedelta

# Create data/mock directory if it doesn't exist
os.makedirs("data/mock", exist_ok=True)

# Definition of the 20 tickers
TICKERS = {
    # FMCG
    "ITC": {"name": "ITC Limited", "sector": "FMCG", "industry": "Cigarettes", "price": 468.25, "cap": 584200, "pe": 27.4, "pb": 6.8, "div": 3.1, "isin": "INE154A01025"},
    "HINDUNILVR": {"name": "Hindustan Unilever Limited", "sector": "FMCG", "industry": "Diversified FMCG", "price": 2450.00, "cap": 575000, "pe": 55.2, "pb": 11.4, "div": 1.8, "isin": "INE030A01027"},
    "BRITANNIA": {"name": "Britannia Industries Limited", "sector": "FMCG", "industry": "Bakery Products", "price": 4900.00, "cap": 118000, "pe": 52.1, "pb": 15.2, "div": 1.5, "isin": "INE216A01030"},
    "NESTLEIND": {"name": "Nestle India Limited", "sector": "FMCG", "industry": "Packaged Foods", "price": 2500.00, "cap": 241000, "pe": 72.4, "pb": 22.1, "div": 1.2, "isin": "INE239A01016"},
    
    # Financials
    "HDFCBANK": {"name": "HDFC Bank Limited", "sector": "Financial Services", "industry": "Private Bank", "price": 1620.00, "cap": 1230000, "pe": 18.2, "pb": 2.8, "div": 1.1, "isin": "INE040A01034"},
    "ICICIBANK": {"name": "ICICI Bank Limited", "sector": "Financial Services", "industry": "Private Bank", "price": 1120.00, "cap": 780000, "pe": 17.5, "pb": 3.1, "div": 0.9, "isin": "INE090A01021"},
    "SBIN": {"name": "State Bank of India", "sector": "Financial Services", "industry": "Public Bank", "price": 820.00, "cap": 730000, "pe": 10.5, "pb": 1.6, "div": 1.7, "isin": "INE062A01020", "high_debt": True},
    "KOTAKBANK": {"name": "Kotak Mahindra Bank Limited", "sector": "Financial Services", "industry": "Private Bank", "price": 1750.00, "cap": 348000, "pe": 21.3, "pb": 3.4, "div": 0.8, "isin": "INE237A01028"},
    
    # IT
    "TCS": {"name": "Tata Consultancy Services Limited", "sector": "Information Technology", "industry": "IT Services", "price": 3850.00, "cap": 1410000, "pe": 29.5, "pb": 12.8, "div": 2.4, "isin": "INE467B01029"},
    "INFY": {"name": "Infosys Limited", "sector": "Information Technology", "industry": "IT Services", "price": 1480.00, "cap": 614000, "pe": 24.1, "pb": 7.5, "div": 2.6, "isin": "INE009A01021"},
    "WIPRO": {"name": "Wipro Limited", "sector": "Information Technology", "industry": "IT Services", "price": 430.00, "cap": 225000, "pe": 21.8, "pb": 3.2, "div": 0.9, "isin": "INE075A01022", "weak_momentum": True, "earnings_decline": True},
    "HCLTECH": {"name": "HCL Technologies Limited", "sector": "Information Technology", "industry": "IT Services", "price": 1320.00, "cap": 358000, "pe": 22.4, "pb": 5.4, "div": 3.2, "isin": "INE860A01027"},
    
    # Energy
    "RELIANCE": {"name": "Reliance Industries Limited", "sector": "Energy", "industry": "Oil & Gas / Diversified", "price": 2950.00, "cap": 1995000, "pe": 28.1, "pb": 2.4, "div": 0.3, "isin": "INE002A01018"},
    "ONGC": {"name": "Oil and Natural Gas Corporation Limited", "sector": "Energy", "industry": "Oil Exploration & Production", "price": 270.00, "cap": 340000, "pe": 7.4, "pb": 1.1, "div": 4.5, "isin": "INE213A01029"},
    "POWERGRID": {"name": "Power Grid Corporation of India Limited", "sector": "Energy", "industry": "Power Transmission", "price": 320.00, "cap": 298000, "pe": 17.1, "pb": 3.2, "div": 3.8, "isin": "INE752E01010", "high_debt": True},
    "NTPC": {"name": "NTPC Limited", "sector": "Energy", "industry": "Power Generation", "price": 360.00, "cap": 349000, "pe": 16.8, "pb": 2.3, "div": 2.1, "isin": "INE733E01010"},
    
    # Auto
    "TATAMOTORS": {"name": "Tata Motors Limited", "sector": "Automobile", "industry": "Commercial & Passenger Vehicles", "price": 980.00, "cap": 358000, "pe": 15.4, "pb": 4.8, "div": 0.6, "isin": "INE155A01022"},
    "M&M": {"name": "Mahindra & Mahindra Limited", "sector": "Automobile", "industry": "Diversified Automobiles", "price": 2800.00, "cap": 348000, "pe": 31.2, "pb": 6.4, "div": 0.8, "isin": "INE101A01026"},
    "MARUTI": {"name": "Maruti Suzuki India Limited", "sector": "Automobile", "industry": "Passenger Cars", "price": 12100.00, "cap": 380000, "pe": 28.9, "pb": 4.9, "div": 1.0, "isin": "INE585B01010"},
    "EICHERMOT": {"name": "Eicher Motors Limited", "sector": "Automobile", "industry": "Two Wheelers", "price": 4700.00, "cap": 129000, "pe": 32.1, "pb": 7.4, "div": 1.1, "isin": "INE066A01013", "promoter_pledge": True}
}

random.seed(42)

def generate_ohlcv(price_start, days, trend_type="neutral"):
    """
    Generates realistic OHLCV bars.
    trend_type can be:
      - 'bullish': steady upward trend (strong momentum)
      - 'bearish': steady downward trend (weak momentum)
      - 'neutral': random walk
    """
    history = []
    current_price = price_start
    
    # We want to go back in time, starting 250 days ago
    start_date = datetime(2026, 6, 19) - timedelta(days=days - 1)
    
    # Set parameters based on trend
    if trend_type == "bullish":
        drift = 0.0012  # average daily return ~0.12%
        vol = 0.015     # daily volatility
    elif trend_type == "bearish":
        drift = -0.0008 # average daily return ~-0.08%
        vol = 0.018     # daily volatility
    else:
        drift = 0.0001
        vol = 0.015
        
    for i in range(days):
        date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Simulate price log-returns
        ret = drift + vol * random.normalvariate(0, 1)
        prev_close = current_price
        current_price = prev_close * (1 + ret)
        
        # Ensure price is positive
        if current_price < 5:
            current_price = 5.0
            
        daily_range = current_price * 0.025 * abs(random.normalvariate(0, 1))
        
        open_p = prev_close
        close_p = current_price
        high_p = max(open_p, close_p) + daily_range * 0.4
        low_p = min(open_p, close_p) - daily_range * 0.4
        
        # Volume generation
        base_vol = 1000000 if price_start > 1000 else 5000000
        vol_factor = random.uniform(0.5, 2.0)
        # Spike volume on bullish days for strong momentum
        if trend_type == "bullish" and close_p > open_p and random.random() > 0.4:
            vol_factor *= random.uniform(1.5, 3.0)
        # Spike volume on bearish days for weak momentum (distribution)
        if trend_type == "bearish" and close_p < open_p and random.random() > 0.4:
            vol_factor *= random.uniform(1.5, 3.0)
            
        volume = int(base_vol * vol_factor)
        delivery_pct = random.uniform(35.0, 65.0)
        
        history.append({
            "date": date_str,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": volume,
            "delivery_pct": round(delivery_pct, 1)
        })
        
    return history

def generate_fundamentals(ticker_code, info):
    # Set default promoter holdings
    promoter_hold = random.uniform(45.0, 65.0)
    # ITC has 0% promoter holding historically
    if ticker_code == "ITC":
        promoter_hold = 0.0
        
    promoter_pledge = 0.0
    if info.get("promoter_pledge"):
        promoter_pledge = random.uniform(22.0, 35.0) # > 20%
        
    debt_equity = random.uniform(0.01, 0.6)
    if info.get("high_debt"):
        debt_equity = random.uniform(1.6, 2.4) # > 1.5
        
    profit_growth = random.uniform(12.0, 28.0)
    if info.get("earnings_decline"):
        profit_growth = random.uniform(-18.0, -5.0) # negative YoY
        
    rev_growth = random.uniform(8.0, 20.0)
    if info.get("earnings_decline"):
        rev_growth = random.uniform(1.0, 6.0)
        
    roce = random.uniform(15.0, 42.0)
    roe = roce * random.uniform(0.8, 0.95)
    
    remaining = 100.0 - promoter_hold
    fii_share = random.uniform(0.15, 0.3)
    dii_share = random.uniform(0.15, 0.25)
    
    fii_hold = remaining * fii_share
    dii_hold = remaining * dii_share
    public_hold = remaining * (1.0 - fii_share - dii_share)
    
    # Explicitly set low float for a couple of stocks
    if ticker_code in ["NESTLEIND", "TCS"]:
        promoter_hold = 73.5
        fii_hold = 15.0
        dii_hold = 8.0
        public_hold = 3.5 # low float triggers (<15%)

    promoter_hold = round(promoter_hold, 1)
    fii_hold = round(fii_hold, 1)
    dii_hold = round(dii_hold, 1)
    public_hold = round(public_hold, 1)
        
    return {
        "ticker": ticker_code,
        "revenue_growth_yoy": round(rev_growth, 1),
        "profit_growth_yoy": round(profit_growth, 1),
        "roce": round(roce, 1),
        "roe": round(roe, 1),
        "debt_to_equity": round(debt_equity, 2),
        "free_cash_flow_cr": round(info["cap"] * random.uniform(0.02, 0.05)),
        "earnings_acceleration": not info.get("earnings_decline"),
        "promoter_holding_pct": promoter_hold,
        "promoter_pledge_pct": promoter_pledge,
        "fii_holding_pct": fii_hold,
        "dii_holding_pct": dii_hold,
        "public_holding_pct": public_hold,
        "as_of_quarter": "Q4FY26"
    }

market_data = {}

for ticker, details in TICKERS.items():
    trend = "neutral"
    if details.get("weak_momentum"):
        trend = "bearish"
    elif ticker in ["RELIANCE", "TCS", "ITC", "TATAMOTORS", "HDFCBANK", "ICICIBANK", "M&M"]:
        trend = "bullish"
        
    history = generate_ohlcv(details["price"], 250, trend)
    latest_close = history[-1]["close"]
    
    # 52 week high/low calculations
    closes = [h["close"] for h in history]
    high52w = max(closes)
    low52w = min(closes)
    
    snapshot = {
        "ticker": ticker,
        "name": details["name"],
        "sector": details["sector"],
        "industry": details["industry"],
        "exchange": "NSE",
        "isin": details["isin"],
        "price": latest_close,
        "open": history[-1]["open"],
        "high": history[-1]["high"],
        "low": history[-1]["low"],
        "prev_close": history[-2]["close"],
        "volume": history[-1]["volume"],
        "market_cap_cr": details["cap"],
        "pe_ratio": details["pe"],
        "pb_ratio": details["pb"],
        "dividend_yield": details["div"],
        "52w_high": round(high52w, 2),
        "52w_low": round(low52w, 2),
        "as_of": "2026-06-19T15:30:00+05:30"
    }
    
    fundamentals = generate_fundamentals(ticker, details)
    
    market_data[ticker] = {
        "snapshot": snapshot,
        "history": history,
        "fundamentals": fundamentals
    }

# Write out to target path
with open("data/mock/market_data.json", "w") as f:
    json.dump(market_data, f, indent=2)

print("Generated mock data for 20 tickers successfully under data/mock/market_data.json.")
