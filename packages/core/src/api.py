import os
import sys
import math
import numpy as np
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Setup python path to find modules in packages/core/src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.mock_provider import MockProvider
from analysis.engine import AnalysisEngine
from agents.workflow import run_agent_pipeline
from db.operations import get_cached_report, save_composite_report, get_screened_momentum_from_db
from models import CompositeReport
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="NSE Agentic Research Platform API",
    description="Core analysis API for Indian stock markets.",
    version="1.0.0"
)

# Instrument the FastAPI app on startup to expose /metrics
Instrumentator().instrument(app).expose(app)

# Enable CORS for Next.js web application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize provider and engine for metadata checks
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.abspath(os.path.join(script_dir, "../../../data/mock/market_data.json"))
provider = MockProvider(data_file=data_path)
engine = AnalysisEngine(provider)

class AnalyzeRequest(BaseModel):
    ticker: str

class ScreenRequest(BaseModel):
    strategy: str = "momentum"
    sector: Optional[str] = None

class CompareRequest(BaseModel):
    tickers: List[str]

class ValuationRequest(BaseModel):
    ticker: str
    method: str = "all"

class BacktestRequest(BaseModel):
    ticker: str
    strategy: str = "triple-ema-crossover"
    capital: float = 1000000
    risk_per_trade: float = 1.0
    commission_pct: float = 0.1

class RiskRequest(BaseModel):
    ticker: str
    risk_free_rate: float = 0.065



@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/analyze", response_model=CompositeReport)
def analyze(req: AnalyzeRequest):
    try:
        ticker = req.ticker.upper().strip()
        
        # Verify ticker existence first
        try:
            provider.get_stock(ticker)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
            
        # Check cache
        report = get_cached_report(ticker)
        
        if report is None:
            # Execute LangGraph Agent workflow
            report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
            # Save to DB cache
            save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
            
        return report
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/screen")
def screen(req: ScreenRequest):
    try:
        if req.strategy != "momentum":
            raise HTTPException(status_code=400, detail="Only 'momentum' strategy is supported in Phase 2.")
        
        # Query cache
        screened = get_screened_momentum_from_db(sector=req.sector)
        
        # Calculate expected number of tickers for this sector or full universe
        expected_count = 20
        if req.sector:
            expected_count = len([t for t in provider.get_all_tickers() if provider.get_stock(t).sector.upper().strip() == req.sector.upper().strip()])
            
        # If cache has fewer items than expected, warm the missing ones
        if len(screened) < expected_count:
            all_screened = engine.screen_momentum(sector=req.sector)
            for stock_data in all_screened:
                ticker = stock_data["ticker"]
                try:
                    report = get_cached_report(ticker)
                    if report is None:
                        report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
                        save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
                except Exception:
                    pass
            
            # Query again from database to get fresh populated rows
            screened = get_screened_momentum_from_db(sector=req.sector)
            
        return screened
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screening failed: {str(e)}")

# ─── Valuation Helpers ──────────────────────────────────────────────────────

def _graham_number(eps: float, book_value: float) -> float:
    if eps is None or book_value is None or eps <= 0 or book_value <= 0:
        return 0
    return round(math.sqrt(22.5 * eps * book_value), 2)

def _simple_dcf(eps: float, growth_rate: float, discount_rate: float = 0.12, terminal_growth: float = 0.04, projection_years: int = 10) -> float:
    if eps is None or eps <= 0 or growth_rate is None:
        return 0
    growth_rate = min(max(growth_rate, 0.0), 0.30)
    total_pv = 0
    projected_eps = eps
    for year in range(1, projection_years + 1):
        projected_eps *= 1 + growth_rate
        if year > 5:
            growth_rate *= 0.9
        pv = projected_eps / ((1 + discount_rate) ** year)
        total_pv += pv
    terminal_eps = projected_eps * (1 + terminal_growth)
    terminal_value = terminal_eps / (discount_rate - terminal_growth)
    terminal_pv = terminal_value / ((1 + discount_rate) ** projection_years)
    return round(total_pv + terminal_pv, 2)

def _pe_relative_value(eps: float, industry_pe: float) -> float:
    if eps is None or industry_pe is None or eps <= 0:
        return 0
    return round(eps * industry_pe, 2)

def _peg_ratio(pe: float, earnings_growth: float) -> float:
    if pe is None or earnings_growth is None or earnings_growth <= 0:
        return 0
    return round(pe / (earnings_growth * 100), 2)

def _get_industry_pe(sector: str) -> float:
    sector_pe = {
        "Technology": 28.0, "Information Technology": 28.0,
        "Financial Services": 18.0, "Financials": 18.0,
        "Consumer Defensive": 45.0, "Consumer Staples": 45.0,
        "Consumer Cyclical": 35.0, "Consumer Discretionary": 35.0,
        "Energy": 12.0, "Healthcare": 30.0, "Industrials": 25.0,
        "Basic Materials": 15.0, "Materials": 15.0,
        "Communication Services": 20.0, "Utilities": 15.0, "Real Estate": 25.0,
    }
    for key, pe in sector_pe.items():
        if key.lower() in sector.lower():
            return pe
    return 20.0

# ─── Endpoints ──────────────────────────────────────────────────────────────

@app.post("/compare")
def compare(req: CompareRequest):
    try:
        reports = []
        for t in req.tickers:
            ticker = t.upper().strip()
            try:
                # Verify ticker existence
                provider.get_stock(ticker)
                
                # Check cache
                report = get_cached_report(ticker)
                if report is None:
                    report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
                    save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
                reports.append(report)
            except ValueError as e:
                reports.append({
                    "ticker": ticker,
                    "error": "NotFoundError",
                    "message": str(e)
                })
            except Exception as e:
                reports.append({
                    "ticker": ticker,
                    "error": "AnalysisError",
                    "message": str(e)
                })
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.post("/valuation")
def valuation(req: ValuationRequest):
    try:
        ticker = req.ticker.upper().strip()
        stock = provider.get_stock(ticker)
        fundamentals = provider.get_fundamentals(ticker)

        cmp = stock.price
        pe = stock.pe_ratio or 0
        pb = stock.pb_ratio or 0
        sector = stock.sector
        industry_pe = _get_industry_pe(sector)

        eps = cmp / pe if pe and pe > 0 else 0
        book_value = cmp / pb if pb and pb > 0 else 0
        earnings_growth = fundamentals.profit_growth_yoy / 100.0 if fundamentals.profit_growth_yoy else 0

        graham = _graham_number(eps, book_value) if eps > 0 and book_value > 0 else 0
        pe_rel = _pe_relative_value(eps, industry_pe) if eps > 0 else 0
        peg = _peg_ratio(pe, earnings_growth) if pe > 0 and earnings_growth > 0 else 0
        growth_for_dcf = earnings_growth if earnings_growth > 0 else 0.10
        dcf_value = _simple_dcf(eps, growth_for_dcf) if eps > 0 else 0

        fair_values = [v for v in [graham, pe_rel, dcf_value] if v > 0]
        avg_fair_value = round(sum(fair_values) / len(fair_values), 2) if fair_values else 0

        margin = ((avg_fair_value - cmp) / avg_fair_value) * 100 if avg_fair_value > 0 else 0
        verdict = "UNDERVALUED" if margin > 20 else "SLIGHTLY UNDERVALUED" if margin > 0 else "FAIRLY VALUED" if margin > -20 else "OVERVALUED" if avg_fair_value > 0 else "INSUFFICIENT_DATA"

        return {
            "ticker": ticker,
            "sector": sector,
            "industry_pe": industry_pe,
            "cmp": cmp,
            "pe_ratio": pe,
            "pb_ratio": pb,
            "dividend_yield": stock.dividend_yield,
            "eps": round(eps, 2),
            "roe": fundamentals.roe,
            "debt_to_equity": fundamentals.debt_to_equity,
            "earnings_growth": fundamentals.profit_growth_yoy,
            "revenue_growth": fundamentals.revenue_growth_yoy,
            "graham_number": graham,
            "pe_relative_value": pe_rel,
            "peg_ratio": peg,
            "dcf_fair_value": dcf_value,
            "avg_fair_value": avg_fair_value,
            "margin_of_safety_pct": round(margin, 1),
            "verdict": verdict,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Valuation failed: {str(e)}")

@app.post("/backtest")
def backtest(req: BacktestRequest):
    try:
        ticker = req.ticker.upper().strip()
        stock = provider.get_stock(ticker)
        history = provider.get_history(ticker, 250)

        if len(history) < 60:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {ticker}: {len(history)} bars (need 60+)")

        dates = pd.date_range(end=pd.Timestamp.now(), periods=len(history), freq="B")
        df = pd.DataFrame({
            "date": dates,
            "open": [h.open for h in history],
            "high": [h.high for h in history],
            "low": [h.low for h in history],
            "close": [h.close for h in history],
            "volume": [h.volume for h in history],
        }).set_index("date")

        df["EMA9"] = df["close"].ewm(span=9, adjust=False).mean()
        df["EMA21"] = df["close"].ewm(span=21, adjust=False).mean()
        df["EMA55"] = df["close"].ewm(span=55, adjust=False).mean()
        df["EMA200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["RSI"] = 100 - 100 / (1 + df["close"].diff().clip(lower=0).rolling(14).mean() / df["close"].diff().clip(upper=0).abs().rolling(14).mean())
        df["ATR"] = pd.concat([df["high"] - df["low"], (df["high"] - df["close"].shift(1)).abs(), (df["low"] - df["close"].shift(1)).abs()], axis=1).max(axis=1).rolling(14).mean()
        df["VOL_SMA20"] = df["volume"].rolling(20).mean()
        df["VOL_RATIO"] = df["volume"] / df["VOL_SMA20"]
        df["HIGHEST_20"] = df["high"].rolling(20).max()
        df["LOWEST_20"] = df["low"].rolling(20).min()
        df["signal"] = 0

        strategy = req.strategy
        if strategy == "triple-ema-crossover":
            for i in range(1, len(df)):
                curr, prev = df.iloc[i], df.iloc[i - 1]
                if pd.isna(curr["EMA9"]) or pd.isna(curr["EMA21"]) or pd.isna(curr["EMA55"]):
                    continue
                if prev["EMA9"] <= prev["EMA21"] and curr["EMA9"] > curr["EMA21"] and curr["EMA9"] > curr["EMA55"] and curr["EMA21"] > curr["EMA55"]:
                    if curr["VOL_RATIO"] > 1.3 if not pd.isna(curr["VOL_RATIO"]) else True:
                        df.iloc[i, df.columns.get_loc("signal")] = 1
                elif prev["EMA9"] >= prev["EMA21"] and curr["EMA9"] < curr["EMA21"]:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
                elif curr["close"] < curr["EMA55"]:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        elif strategy == "rsi-mean-reversion":
            for i in range(1, len(df)):
                curr = df.iloc[i]
                if pd.isna(curr["RSI"]) or pd.isna(curr["EMA200"]):
                    continue
                if curr["RSI"] < 30 and curr["close"] > curr["EMA200"]:
                    df.iloc[i, df.columns.get_loc("signal")] = 1
                elif curr["RSI"] > 70:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        elif strategy == "breakout-retest":
            broke_out = False
            breakout_level = 0.0
            for i in range(2, len(df)):
                curr, prev = df.iloc[i], df.iloc[i - 1]
                if pd.isna(curr["HIGHEST_20"]):
                    continue
                if not broke_out and curr["close"] > prev["HIGHEST_20"]:
                    broke_out = True
                    breakout_level = prev["HIGHEST_20"]
                elif broke_out:
                    if curr["low"] <= breakout_level * 1.01 and curr["close"] > breakout_level:
                        df.iloc[i, df.columns.get_loc("signal")] = 1
                        broke_out = False
                    elif curr["close"] < breakout_level * 0.98:
                        broke_out = False
                if not pd.isna(curr["LOWEST_20"]) and curr["close"] < curr["LOWEST_20"]:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        elif strategy == "ema-pullback":
            for i in range(2, len(df)):
                curr, prev = df.iloc[i], df.iloc[i - 1]
                if pd.isna(curr["EMA9"]) or pd.isna(curr["EMA21"]) or pd.isna(curr["EMA55"]):
                    continue
                if curr["EMA9"] > curr["EMA21"] > curr["EMA55"]:
                    if prev["low"] <= prev["EMA21"] * 1.005 and curr["close"] > curr["EMA21"]:
                        df.iloc[i, df.columns.get_loc("signal")] = 1
                if curr["close"] < curr["EMA55"]:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}. Available: triple-ema-crossover, rsi-mean-reversion, breakout-retest, ema-pullback")

        trades = []
        position = None
        current_capital = req.capital
        for i in range(len(df)):
            row, date = df.iloc[i], df.index[i]
            if row["signal"] == 1 and position is None:
                entry_price = row["close"]
                atr = row["ATR"] if not pd.isna(row["ATR"]) else entry_price * 0.02
                stop_loss = entry_price - 2 * atr
                risk_amount = current_capital * (req.risk_per_trade / 100)
                risk_per_share = entry_price - stop_loss
                if risk_per_share <= 0:
                    continue
                qty = int(risk_amount / risk_per_share)
                if qty <= 0:
                    continue
                commission = entry_price * qty * (req.commission_pct / 100)
                position = {"entry_date": date, "entry_price": entry_price, "stop_loss": stop_loss, "qty": qty, "entry_commission": commission}
            elif row["signal"] == -1 and position is not None:
                exit_price = row["close"]
                commission = exit_price * position["qty"] * (req.commission_pct / 100)
                pnl = (exit_price - position["entry_price"]) * position["qty"] - position["entry_commission"] - commission
                current_capital += pnl
                trades.append({"entry_date": position["entry_date"].strftime("%Y-%m-%d"), "exit_date": date.strftime("%Y-%m-%d"), "entry_price": round(position["entry_price"], 2), "exit_price": round(exit_price, 2), "qty": position["qty"], "pnl": round(pnl, 2), "return_pct": round((exit_price / position["entry_price"] - 1) * 100, 2), "holding_days": (date - position["entry_date"]).days})
                position = None
            elif position is not None and row["low"] <= position["stop_loss"]:
                exit_price = position["stop_loss"]
                commission = exit_price * position["qty"] * (req.commission_pct / 100)
                pnl = (exit_price - position["entry_price"]) * position["qty"] - position["entry_commission"] - commission
                current_capital += pnl
                trades.append({"entry_date": position["entry_date"].strftime("%Y-%m-%d"), "exit_date": date.strftime("%Y-%m-%d"), "entry_price": round(position["entry_price"], 2), "exit_price": round(exit_price, 2), "qty": position["qty"], "pnl": round(pnl, 2), "return_pct": round((exit_price / position["entry_price"] - 1) * 100, 2), "holding_days": (date - position["entry_date"]).days, "stopped_out": True})
                position = None
        if position is not None:
            exit_price = df.iloc[-1]["close"]
            commission = exit_price * position["qty"] * (req.commission_pct / 100)
            pnl = (exit_price - position["entry_price"]) * position["qty"] - position["entry_commission"] - commission
            current_capital += pnl
            trades.append({"entry_date": position["entry_date"].strftime("%Y-%m-%d"), "exit_date": df.index[-1].strftime("%Y-%m-%d"), "entry_price": round(position["entry_price"], 2), "exit_price": round(exit_price, 2), "qty": position["qty"], "pnl": round(pnl, 2), "return_pct": round((exit_price / position["entry_price"] - 1) * 100, 2), "holding_days": (df.index[-1] - position["entry_date"]).days, "open_trade": True})

        total_trades = len(trades)
        if total_trades == 0:
            return {"ticker": ticker, "strategy": strategy, "total_trades": 0, "message": "No trades generated."}
        winning = [t for t in trades if t["pnl"] > 0]
        losing = [t for t in trades if t["pnl"] <= 0]
        win_rate = len(winning) / total_trades * 100
        total_return = (current_capital / req.capital - 1) * 100
        trading_days = (df.index[-1] - df.index[0]).days
        years = trading_days / 365.25
        cagr = ((current_capital / req.capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        avg_win = np.mean([t["pnl"] for t in winning]) if winning else 0
        avg_loss = abs(np.mean([t["pnl"] for t in losing])) if losing else 1
        profit_factor = sum(t["pnl"] for t in winning) / abs(sum(t["pnl"] for t in losing)) if losing and sum(t["pnl"] for t in losing) != 0 else float("inf")
        equity = [req.capital]
        for t in trades:
            equity.append(equity[-1] + t["pnl"])
        equity_s = pd.Series(equity)
        max_drawdown = ((equity_s - equity_s.cummax()) / equity_s.cummax() * 100).min()
        avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
        avg_holding = np.mean([t["holding_days"] for t in trades])

        return {
            "ticker": ticker, "strategy": strategy,
            "period_start": df.index[0].strftime("%Y-%m-%d"), "period_end": df.index[-1].strftime("%Y-%m-%d"),
            "starting_capital": req.capital, "ending_capital": round(current_capital, 2),
            "total_return": round(total_return, 2), "cagr": round(cagr, 2),
            "max_drawdown": round(max_drawdown, 2), "sharpe_ratio": 0,
            "total_trades": total_trades, "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "∞",
            "avg_holding_days": round(avg_holding, 1), "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2), "risk_reward": f"1:{avg_rr:.1f}",
            "total_pnl": round(current_capital - req.capital, 2),
            "trades": trades[-20:],
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@app.post("/risk")
def risk_analysis(req: RiskRequest):
    try:
        ticker = req.ticker.upper().strip()
        stock = provider.get_stock(ticker)
        history = provider.get_history(ticker, 250)

        if len(history) < 20:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {ticker}: {len(history)} bars (need 20+)")

        closes = np.array([h.close for h in history])
        returns = np.diff(closes) / closes[:-1]
        daily_rf = req.risk_free_rate / 252

        total_return = (closes[-1] / closes[0] - 1) * 100
        annual_return = total_return * (252 / len(returns))
        volatility = float(np.std(returns) * np.sqrt(252) * 100)
        beta = 1.0  # Simplified - no NIFTY data in mock
        var_95 = float(np.percentile(returns, 5) * 100)
        var_99 = float(np.percentile(returns, 1) * 100)
        cum_max = np.maximum.accumulate(closes)
        drawdown = (closes - cum_max) / cum_max * 100
        max_drawdown = float(np.min(drawdown))
        excess_return = np.mean(returns) - daily_rf
        std_return = float(np.std(returns))
        sharpe = (excess_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        downside_returns = returns[returns < 0]
        downside_std = float(np.std(downside_returns)) if len(downside_returns) > 0 else 0.001
        sortino = (excess_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0

        risk_score = 0
        risk_score += min(30, volatility * 0.5)
        risk_score += min(20, abs(max_drawdown) * 0.8)
        risk_score += min(15, max(0, (beta - 1) * 30))
        risk_score += min(15, abs(var_95) * 3)
        if sharpe < 0.5:
            risk_score += 10
        elif sharpe < 1.0:
            risk_score += 5
        risk_score += min(10, max(0, 50 - total_return) * 0.2)
        risk_score = min(100, max(0, round(risk_score)))

        if risk_score <= 40:
            rating = "Low Risk"
        elif risk_score <= 70:
            rating = "Moderate Risk"
        else:
            rating = "High Risk"

        return {
            "ticker": ticker, "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2), "volatility": round(volatility, 2),
            "beta": round(beta, 2), "var_95_daily": round(var_95, 2),
            "var_99_daily": round(var_99, 2), "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2), "sortino_ratio": round(sortino, 2),
            "risk_score": risk_score, "rating": rating,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")
