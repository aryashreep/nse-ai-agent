import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from models import (
    CompositeReport, TechnicalMetrics, MomentumMetrics,
    RiskMetrics, ValuationMetrics
)
from data.mock_provider import MockProvider

class AnalysisEngine:
    def __init__(self, provider: MockProvider):
        self.provider = provider
        # Cache RS scores and velocities for the universe to avoid recomputation
        self._rs_scores: Dict[str, float] = {}
        self._rs_velocities: Dict[str, float] = {}
        self._sector_rs: Dict[str, float] = {}
        self.compute_universe_relative_strength()

    def compute_universe_relative_strength(self):
        """
        Computes Relative Strength (RS) scores for all tickers in the provider.
        RS score is the percentile rank (0-100) of 125-day return.
        RS velocity is the rate of change over the last 20 days.
        """
        tickers = self.provider.get_all_tickers()
        returns: Dict[str, float] = {}
        returns_prev: Dict[str, float] = {} # returns 20 days ago

        for ticker in tickers:
            try:
                history = self.provider.get_history(ticker, 250)
                if len(history) < 150:
                    returns[ticker] = 0.0
                    returns_prev[ticker] = 0.0
                    continue
                
                closes = [h.close for h in history]
                # Current return (last 125 days)
                ret = (closes[-1] - closes[-125]) / closes[-125]
                returns[ticker] = ret

                # Return 20 days ago (125-day return starting 20 days ago)
                ret_prev = (closes[-21] - closes[-145]) / closes[-145]
                returns_prev[ticker] = ret_prev
            except Exception:
                returns[ticker] = 0.0
                returns_prev[ticker] = 0.0

        # Rank current returns to get RS score (0 to 100)
        sorted_tickers = sorted(tickers, key=lambda t: returns[t])
        n = len(sorted_tickers)
        for idx, ticker in enumerate(sorted_tickers):
            # Convert rank to percentile
            percentile = (idx / (n - 1)) * 100 if n > 1 else 50.0
            self._rs_scores[ticker] = round(percentile, 1)

        # Rank previous returns to get previous RS score
        sorted_tickers_prev = sorted(tickers, key=lambda t: returns_prev[t])
        rs_scores_prev = {}
        for idx, ticker in enumerate(sorted_tickers_prev):
            percentile = (idx / (n - 1)) * 100 if n > 1 else 50.0
            rs_scores_prev[ticker] = percentile

        # Compute velocity (change in RS score over last 20 days)
        for ticker in tickers:
            self._rs_velocities[ticker] = round(self._rs_scores[ticker] - rs_scores_prev.get(ticker, 50.0), 2)

        # Calculate average RS score per sector
        sector_totals: Dict[str, List[float]] = {}
        for ticker in tickers:
            try:
                stock = self.provider.get_stock(ticker)
                sector = stock.sector
                if sector not in sector_totals:
                    sector_totals[sector] = []
                sector_totals[sector].append(self._rs_scores[ticker])
            except Exception:
                pass

        for sector, scores in sector_totals.items():
            self._sector_rs[sector] = round(sum(scores) / len(scores), 1)

    def get_rs_score(self, ticker: str) -> float:
        return self._rs_scores.get(ticker.upper(), 50.0)

    def get_rs_velocity(self, ticker: str) -> float:
        return self._rs_velocities.get(ticker.upper(), 0.0)

    def get_sector_rs(self, sector: str) -> float:
        return self._sector_rs.get(sector, 50.0)

    def run_analysis(self, ticker: str) -> CompositeReport:
        ticker = ticker.upper().strip()
        stock = self.provider.get_stock(ticker)
        history = self.provider.get_history(ticker, 250)
        fundamentals = self.provider.get_fundamentals(ticker)

        # Convert history list to pandas DataFrame for calculations
        df = pd.DataFrame([h.dict() for h in history])

        # 1. Technical calculations
        df["ema_21"] = df["close"].ewm(span=21, adjust=False).mean()
        df["ema_55"] = df["close"].ewm(span=55, adjust=False).mean()
        df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()

        # Volume Expansion: 20-day average volume
        df["vol_sma20"] = df["volume"].rolling(20).mean()

        # True Range and ATR (Average True Range)
        df["prev_close"] = df["close"].shift(1)
        df["tr"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                (df["high"] - df["prev_close"]).abs(),
                (df["low"] - df["prev_close"]).abs()
            )
        )
        df["atr"] = df["tr"].rolling(14).mean()
        df["atr_sma20"] = df["atr"].rolling(20).mean()

        # Distribution days logic
        df["is_down_day"] = df["close"] < df["open"]
        df["is_high_volume"] = df["volume"] > df["vol_sma20"]
        df["is_distribution"] = df["is_down_day"] & df["is_high_volume"]

        # Now extract the latest bar
        latest = df.iloc[-1]
        price = latest["close"]
        ema21 = latest["ema_21"]
        ema55 = latest["ema_55"]
        ema200 = latest["ema_200"]
        ema9 = latest["ema_9"]

        price_vs_ema200_pct = ((price - ema200) / ema200) * 100

        # Trend detection
        if ema9 > ema21 > ema55 and price > ema200:
            trend = "bullish"
        elif ema9 < ema21 < ema55 and price < ema200:
            trend = "bearish"
        else:
            trend = "neutral"

        technical = TechnicalMetrics(
            ema_21=round(ema21, 2),
            ema_55=round(ema55, 2),
            ema_200=round(ema200, 2),
            price_vs_ema200_pct=round(price_vs_ema200_pct, 1),
            trend=trend
        )

        # 2. Momentum calculations
        rs_score = self.get_rs_score(ticker)
        rs_velocity = self.get_rs_velocity(ticker)
        volume_expansion = latest["volume"] > 1.5 * latest["vol_sma20"]

        latest_atr = latest["atr"] if not pd.isna(latest["atr"]) else price * 0.02
        latest_atr_sma20 = latest["atr_sma20"] if not pd.isna(latest["atr_sma20"]) else latest_atr
        atr_expansion = latest_atr > 1.2 * latest_atr_sma20

        # Composite Momentum Score
        trend_score = 100 if trend == "bullish" else (0 if trend == "bearish" else 50)
        norm_ema200_pct = min(100, max(0, (price_vs_ema200_pct + 10) * 4)) # normalize -10% to +15%
        norm_velocity = min(100, max(0, (rs_velocity + 20) * 2.5)) # normalize -20 to +20
        
        momentum_score = (rs_score * 0.5) + (norm_velocity * 0.2) + (norm_ema200_pct * 0.2) + (trend_score * 0.1)
        momentum_score = round(min(100.0, max(0.0, momentum_score)), 1)

        momentum = MomentumMetrics(
            rs_score=rs_score,
            rs_velocity=rs_velocity,
            volume_expansion=bool(volume_expansion),
            atr_expansion=bool(atr_expansion),
            momentum_score=momentum_score
        )

        # 3. Risk Flag calculations
        flags = []
        if fundamentals.debt_to_equity > 1.5:
            flags.append("HIGH_DEBT")
        if fundamentals.promoter_pledge_pct > 20.0:
            flags.append("PROMOTER_PLEDGE")
        if fundamentals.profit_growth_yoy < 0.0:
            flags.append("EARNINGS_DECLINE")
        if fundamentals.public_holding_pct < 15.0:
            flags.append("LOW_FLOAT")

        # Sector weakness: Sector RS < 30
        sector_rs = self.get_sector_rs(stock.sector)
        if sector_rs < 30.0:
            flags.append("SECTOR_WEAKNESS")

        # Volatility expansion: ATR > 30% above 20-day average
        if latest_atr > 1.3 * latest_atr_sma20:
            flags.append("VOLATILITY_EXPANSION")

        # Distribution: Volume expanding on down days for 3 consecutive days
        consec_distribution = 0
        for val in reversed(df["is_distribution"].tolist()[-5:]): # check last 5 days
            if val:
                consec_distribution += 1
            else:
                break
        if consec_distribution >= 3:
            flags.append("DISTRIBUTION")

        # FII Exit: FII holding declining (since mock data is static, we tag WIPRO for simulation if FII < 20%)
        if ticker == "WIPRO":
            flags.append("FII_EXIT")

        atr_pct = (latest_atr / price) * 100
        drawdown = ((stock.fifty_two_week_high - price) / stock.fifty_two_week_high) * 100

        risk = RiskMetrics(
            flags=flags,
            atr_pct=round(atr_pct, 2),
            drawdown_from_52w_high_pct=round(drawdown, 1)
        )

        # 4. Valuation
        valuation = ValuationMetrics(
            pe_ratio=stock.pe_ratio,
            pb_ratio=stock.pb_ratio,
            dividend_yield=stock.dividend_yield
        )

        disclaimer = (
            "This platform provides educational and research information only. "
            "It does not provide personalized investment advice. Past performance does not "
            "guarantee future results. Consult a SEBI-registered investment advisor before "
            "making investment decisions."
        )

        return CompositeReport(
            ticker=ticker,
            as_of=stock.as_of,
            source="mock",
            technical=technical,
            momentum=momentum,
            risk=risk,
            valuation=valuation,
            disclaimer=disclaimer
        )


    def screen_momentum(self, sector: str = None) -> List[Dict[str, Any]]:
        """
        Screens the universe for momentum.
        Returns ranked list of tickers with their momentum scores.
        """
        tickers = self.provider.get_all_tickers()
        results = []

        for ticker in tickers:
            try:
                stock = self.provider.get_stock(ticker)
                # Filter by sector if provided
                if sector and stock.sector.upper().strip() != sector.upper().strip():
                    continue

                report = self.run_analysis(ticker)
                results.append({
                    "ticker": ticker,
                    "name": stock.name,
                    "sector": stock.sector,
                    "price": stock.price,
                    "momentum_score": report.momentum.momentum_score,
                    "rs_score": report.momentum.rs_score,
                    "trend": report.technical.trend,
                    "risk_flags": report.risk.flags
                })
            except Exception:
                pass

        # Sort by momentum score descending
        results = sorted(results, key=lambda x: x["momentum_score"], reverse=True)
        return results
