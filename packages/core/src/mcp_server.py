import os
import sys
import json
from typing import List, Optional, Dict, Any

# Setup python path to find modules in packages/core/src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from data.mock_provider import MockProvider
from analysis.engine import AnalysisEngine
from agents.workflow import run_agent_pipeline
from db.operations import get_cached_report, save_composite_report, get_screened_momentum_from_db
from models import CompositeReport

# Create FastMCP server instance
mcp = FastMCP("nse-ai-agent")

# Resolve mock data provider and engine
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.abspath(os.path.join(script_dir, "../../../data/mock/market_data.json"))
provider = MockProvider(data_file=data_path)
engine = AnalysisEngine(provider)

def get_or_run_report(ticker: str) -> CompositeReport:
    ticker = ticker.upper().strip()
    # Check if stock exists
    provider.get_stock(ticker)
    
    # Check cache
    report = get_cached_report(ticker)
    if report is None:
        # Cache miss: run pipeline and save
        report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
        save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
        
    return report

@mcp.tool()
def analyze_stock(ticker: str) -> str:
    """
    Perform a complete multi-agent momentum, technical, valuation, and risk flag analysis 
    on an NSE (Indian stock market) ticker (e.g. RELIANCE, TCS, ITC).
    """
    try:
        report = get_or_run_report(ticker)
        
        # Format the result as markdown
        trend_indicator = "🟢 Bullish" if report.technical.trend == "bullish" else "🔴 Bearish" if report.technical.trend == "bearish" else "🟡 Neutral"
        flags_str = ", ".join([f"`{f}`" for f in report.risk.flags]) if report.risk.flags else "None (Low Risk)"
        
        md = f"""# NSE Stock Analysis: {report.ticker}

**Date/Time of Analysis:** {report.as_of}
**Data Source:** {report.source.upper()}

## 📈 Technical Snapshot
* **Trend:** {trend_indicator}
* **EMA Alignment:** 
  * 21 EMA: ₹{report.technical.ema_21}
  * 55 EMA: ₹{report.technical.ema_55}
  * 200 EMA: ₹{report.technical.ema_200}
* **Distance vs 200 EMA:** `{report.technical.price_vs_ema200_pct}%`

## 🚀 Momentum Profile
* **Composite Momentum Score:** `{report.momentum.momentum_score}/100`
* **Relative Strength (RS) Score:** `{report.momentum.rs_score}/100` (vs Nifty 500 universe)
* **RS Velocity:** `{report.momentum.rs_velocity}` (20-day ROC of RS)
* **Volume Expansion (SMA20):** {"✅ Yes (Expanding)" if report.momentum.volume_expansion else "❌ No"}
* **Volatility Expansion (ATR):** {"⚠️ Yes (ATR expanding)" if report.momentum.atr_expansion else "❌ No"}

## ⚖️ Valuation Multiples
* **P/E Ratio:** {f"{report.valuation.pe_ratio}x" if report.valuation.pe_ratio else "N/A"}
* **P/B Ratio:** {f"{report.valuation.pb_ratio}x" if report.valuation.pb_ratio else "N/A"}
* **Dividend Yield:** {f"{report.valuation.dividend_yield}%" if report.valuation.dividend_yield else "N/A"}

## 🚨 Risk Flag Audit
* **Daily Volatility (ATR%):** `{report.risk.atr_pct}%`
* **Drawdown from 52w High:** `{report.risk.drawdown_from_52w_high_pct}%`
* **Active Risk Flags:** {flags_str}

---
⚠️ **DISCLAIMER:** {report.disclaimer}
"""
        return md
    except ValueError as e:
        return f"⚠️ Error: Ticker '{ticker}' is invalid or not in our mock universe. Error details: {str(e)}"
    except Exception as e:
        return f"⚠️ Error occurred during analysis of '{ticker}': {str(e)}"

@mcp.tool()
def screen_momentum(sector: Optional[str] = None) -> str:
    """
    Screen the NSE stock universe for momentum opportunities. 
    Optionally filter by sector (e.g. FMCG, Financial Services, Information Technology, Energy, Automobile).
    """
    try:
        # Verify and warm cache if needed
        expected_count = 20
        if sector:
            expected_count = len([t for t in provider.get_all_tickers() if provider.get_stock(t).sector.upper().strip() == sector.upper().strip()])
            
        screened = get_screened_momentum_from_db(sector=sector)
        
        if len(screened) < expected_count:
            # Warm up cache
            all_screened = engine.screen_momentum(sector=sector)
            for stock_data in all_screened:
                ticker = stock_data["ticker"]
                try:
                    get_or_run_report(ticker)
                except Exception:
                    pass
            # Query again
            screened = get_screened_momentum_from_db(sector=sector)

        if not screened:
            return "No matching momentum opportunities found."

        # Format as markdown table
        lines = [
            f"# Momentum Screener Results" + (f" (Sector: {sector})" if sector else ""),
            "",
            "| Rank | Ticker | Sector | Price | Trend | Mom. Score | Risk Flags |",
            "|------|--------|--------|-------|-------|------------|------------|"
        ]
        
        for idx, stock in enumerate(screened):
            trend_str = "🟢 BULLISH" if stock["trend"] == "bullish" else "🔴 BEARISH" if stock["trend"] == "bearish" else "🟡 NEUTRAL"
            flags = ", ".join([f"`{f}`" for f in stock["risk_flags"]]) if stock["risk_flags"] else "None"
            lines.append(
                f"| {idx + 1} | **{stock['ticker']}** | {stock['sector']} | ₹{stock['price'] or 'N/A'} | {trend_str} | **{stock['momentum_score']}/100** | {flags} |"
            )
            
        lines.append("\n⚠️ *Disclaimer: For educational/research purposes only. Consult a SEBI-registered advisor before trading.*")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Error running momentum screener: {str(e)}"

@mcp.tool()
def compare_stocks(tickers: List[str]) -> str:
    """
    Compare multiple NSE stock tickers side-by-side across trend, momentum scores, 
    P/E ratio, and drawdowns.
    """
    try:
        reports = []
        for t in tickers:
            ticker = t.upper().strip()
            try:
                report = get_or_run_report(ticker)
                reports.append(report)
            except Exception as e:
                # Add dummy report indicating error
                pass
                
        if not reports:
            return "No valid tickers could be resolved for comparison."
            
        # Format as side-by-side markdown table
        lines = [
            "# Stock Comparison Board",
            "",
            "| Ticker | Trend | Momentum Score | RS Score | RS Velocity | P/E Ratio | Drawdown | Active Risk Flags |",
            "|--------|-------|----------------|----------|-------------|-----------|----------|-------------------|Standard"
        ]
        
        for r in reports:
            trend_str = "🟢 BULLISH" if r.technical.trend == "bullish" else "🔴 BEARISH" if r.technical.trend == "bearish" else "🟡 NEUTRAL"
            pe_str = f"{r.valuation.pe_ratio}x" if r.valuation.pe_ratio else "N/A"
            flags = ", ".join([f"`{f}`" for f in r.risk.flags]) if r.risk.flags else "None"
            
            lines.append(
                f"| **{r.ticker}** | {trend_str} | **{r.momentum.momentum_score}/100** | {r.momentum.rs_score}/100 | {r.momentum.rs_velocity} | {pe_str} | -{r.risk.drawdown_from_52w_high_pct}% | {flags} |"
            )
            
        lines.append("\n⚠️ *Disclaimer: For educational/research purposes only. Consult a SEBI-registered advisor before trading.*")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Error comparing stocks: {str(e)}"

@mcp.tool()
def sector_rotation() -> str:
    """
    Identify and rank market sectors based on average Relative Strength (RS) momentum scores 
    to pinpoint leading, improving, or weakening sectors.
    """
    try:
        # Precompute RS scores
        engine.compute_universe_relative_strength()
        sectors_rs = engine._sector_rs
        
        # Sort sectors by RS Score
        sorted_sectors = sorted(sectors_rs.items(), key=lambda x: x[1], reverse=True)
        
        lines = [
            "# Sector Rotation Quadrant Analysis",
            "",
            "| Quadrant | Sector | Average RS Score | Status Description |",
            "|----------|--------|------------------|--------------------|"
        ]
        
        for sector, rs in sorted_sectors:
            if rs >= 60.0:
                quad = "🔥 **Leading**"
                status = "Strong sector momentum; outperforming the index universe. Accumulation phase."
            elif rs >= 45.0:
                quad = "📈 **Improving**"
                status = "Gaining relative strength. Potential breakout phase."
            elif rs >= 30.0:
                quad = "🟡 **Weakening**"
                status = "Losing momentum; profit booking observed. Avoid fresh entries."
            else:
                quad = "❄️ **Lagging**"
                status = "Underperforming segment. Distribution phase active."
                
            lines.append(f"| {quad} | **{sector}** | `{rs}/100` | {status} |")
            
        lines.append("\n⚠️ *Disclaimer: For educational/research purposes only. Consult a SEBI-registered advisor before trading.*")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Error running sector rotation: {str(e)}"

@mcp.tool()
def portfolio_review(tickers: List[str]) -> str:
    """
    Audit a list of stock tickers in a portfolio, flagging high-debt, promoter pledge, 
    or severe drawdown risks.
    """
    try:
        reports = []
        for t in tickers:
            ticker = t.upper().strip()
            try:
                report = get_or_run_report(ticker)
                reports.append(report)
            except Exception:
                pass
                
        if not reports:
            return "No valid tickers could be resolved for portfolio review."
            
        lines = [
            "# Portfolio Risk Audit",
            "",
            "| Ticker | Drawdown | ATR (Vol) | Active Risk Warnings |",
            "|--------|----------|-----------|----------------------|"
        ]
        
        total_flags_count = 0
        extreme_drawdown_count = 0
        
        for r in reports:
            drawdown = r.risk.drawdown_from_52w_high_pct
            flags = r.risk.flags
            
            # Count metrics
            total_flags_count += len(flags)
            if drawdown > 20.0:
                extreme_drawdown_count += 1
                
            flags_str = ", ".join([f"🚨 **{f}**" for f in flags]) if flags else "✅ No Flags"
            lines.append(f"| **{r.ticker}** | -{drawdown}% | {r.risk.atr_pct}% | {flags_str} |")
            
        lines.append("")
        lines.append("## Summary Recommendations")
        
        if total_flags_count > 3:
            lines.append("* ⚠️ **High Risk Concentration:** Your portfolio has multiple active risk warnings. Consider rebalancing away from highly leveraged (`HIGH_DEBT`) or underperforming (`SECTOR_WEAKNESS`) stocks.")
        else:
            lines.append("* 🟢 **Healthy Risk Profile:** Risk flags are minimal and within acceptable thresholds.")
            
        if extreme_drawdown_count > 0:
            lines.append(f"* ⚠️ **Severe Drawdowns:** {extreme_drawdown_count} stock(s) are trading at >20% below their 52-week highs. Verify structural integrity of these businesses.")
            
        lines.append("\n⚠️ *Disclaimer: This platform provides educational and research information only. Consult a SEBI-registered advisor before trading.*")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Error performing portfolio review: {str(e)}"

if __name__ == "__main__":
    mcp.run()
