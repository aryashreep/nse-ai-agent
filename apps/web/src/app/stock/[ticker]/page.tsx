"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { analyzeStock, CompositeReport, getPredictInclusion, IndexInclusionPrediction } from "../../../services/api";


export default function StockDetail() {
  const params = useParams();
  const router = useRouter();
  const ticker = params.ticker as string;
  const [report, setReport] = useState<CompositeReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [isWatchlisted, setIsWatchlisted] = useState(false);
  const [prediction, setPrediction] = useState<IndexInclusionPrediction | null>(null);
  const [predLoading, setPredLoading] = useState(false);
  const [predError, setPredError] = useState("");


  useEffect(() => {
    async function loadReport() {
      if (!ticker) return;
      try {
        setLoading(true);
        const data = await analyzeStock(ticker);
        setReport(data);
        
        // Check if watchlisted
        const saved = localStorage.getItem("nse_watchlist");
        if (saved) {
          const parsed = JSON.parse(saved) as string[];
          setIsWatchlisted(parsed.includes(ticker.toUpperCase()));
        }
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to load stock data");
      } finally {
        setLoading(false);
      }
    }

    async function loadPrediction() {
      if (!ticker) return;
      try {
        setPredLoading(true);
        setPredError("");
        const data = await getPredictInclusion(ticker);
        setPrediction(data);
      } catch (err: any) {
        setPredError(err.message || "Predictor server offline");
      } finally {
        setPredLoading(false);
      }
    }

    loadReport();
    loadPrediction();
  }, [ticker]);

  const toggleWatchlist = () => {
    const symbol = ticker.toUpperCase();
    const saved = localStorage.getItem("nse_watchlist");
    let list: string[] = [];
    if (saved) {
      list = JSON.parse(saved) as string[];
    }
    
    if (list.includes(symbol)) {
      list = list.filter((s) => s !== symbol);
      setIsWatchlisted(false);
    } else {
      list.push(symbol);
      setIsWatchlisted(true);
    }
    localStorage.setItem("nse_watchlist", JSON.stringify(list));
  };

  if (loading) {
    return (
      <div style={{ padding: "8rem 2rem", textAlign: "center", color: "var(--text-secondary)" }}>
        <h2>Running autonomous multi-agent analysis for {ticker?.toUpperCase()}...</h2>
        <p style={{ marginTop: "1rem" }}>Retrieving snapshots and executing state graph nodes.</p>
      </div>
    );
  }

  if (errorMsg || !report) {
    return (
      <div style={{ padding: "4rem 2rem", textAlign: "center" }}>
        <h2 style={{ color: "var(--accent-rose)" }}>⚠️ Analysis Error</h2>
        <p style={{ marginTop: "1rem", color: "var(--text-secondary)" }}>{errorMsg || `Stock ticker '${ticker}' could not be resolved.`}</p>
        <div style={{ marginTop: "2rem" }}>
          <Link href="/" className="btn-secondary">Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  const trendColor = report.technical.trend === "bullish" ? "var(--accent-emerald)" : report.technical.trend === "bearish" ? "var(--accent-rose)" : "var(--accent-amber)";
  const trendClass = report.technical.trend === "bullish" ? "badge-bullish" : report.technical.trend === "bearish" ? "badge-bearish" : "badge-neutral";

  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <Link href="/" className="btn-secondary" style={{ padding: "0.4rem 0.8rem", fontSize: "0.85rem" }}>
          &larr; Dashboard
        </Link>
      </div>

      {/* Header section */}
      <div className="stock-detail-header">
        <div className="stock-title-section">
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <h1 style={{ fontSize: "2.5rem" }}>{report.ticker}</h1>
            <span className={`badge ${trendClass}`} style={{ fontSize: "0.85rem", padding: "0.3rem 0.6rem" }}>
              {report.technical.trend.toUpperCase()} TREND
            </span>
          </div>
          <h2 style={{ fontWeight: "400", fontSize: "1.25rem", color: "var(--text-secondary)" }}>
            ISIN: {report.ticker} | Sector: {report.source === "db_cache" ? "Loaded from SQLite Cache" : "Fresh Mock Data"}
          </h2>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button className="btn-secondary" onClick={toggleWatchlist}>
            {isWatchlisted ? "⭐ Watchlisted" : "☆ Add to Watchlist"}
          </button>
        </div>
      </div>

      <div className="grid-cols-2" style={{ marginBottom: "2rem" }}>
        {/* Technical Gauge Card */}
        <div className="card">
          <h2>📊 Technical Alignment</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.5rem" }}>
            <div className="metric-row">
              <span className="metric-label">Trend Structure</span>
              <span className="metric-val" style={{ color: trendColor }}>{report.technical.trend.toUpperCase()}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">21 / 55 Exponential Moving Average</span>
              <span className="metric-val">₹{report.technical.ema_21} / ₹{report.technical.ema_55}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">200 Exponential Moving Average</span>
              <span className="metric-val">₹{report.technical.ema_200}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Price distance vs 200 EMA</span>
              <span className="metric-val" style={{ color: report.technical.price_vs_ema200_pct > 0 ? "var(--accent-emerald)" : "var(--accent-rose)" }}>
                {report.technical.price_vs_ema200_pct > 0 ? "+" : ""}{report.technical.price_vs_ema200_pct}%
              </span>
            </div>
          </div>
        </div>

        {/* Momentum Scores Card */}
        <div className="card">
          <h2>🚀 Momentum Indicators</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.5rem" }}>
            <div className="metric-row">
              <span className="metric-label">Composite Momentum Score</span>
              <span className="metric-val" style={{ color: "var(--accent-purple)", fontSize: "1.2rem" }}>
                {report.momentum.momentum_score}/100
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Relative Strength (RS) Percentile</span>
              <span className="metric-val">{report.momentum.rs_score}/100</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">RS Velocity (Rate of Change)</span>
              <span className="metric-val" style={{ color: report.momentum.rs_velocity > 0 ? "var(--accent-emerald)" : "var(--accent-rose)" }}>
                {report.momentum.rs_velocity > 0 ? "+" : ""}{report.momentum.rs_velocity}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Volume Breakout (SMA 20)</span>
              <span className="metric-val">{report.momentum.volume_expansion ? "🟢 Expanding" : "⚪ Normal"}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-cols-2" style={{ marginBottom: "2rem" }}>
        {/* Valuation Multiples */}
        <div className="card">
          <h2>⚖️ Valuation Multiples</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.5rem" }}>
            <div className="metric-row">
              <span className="metric-label">Price to Earnings (P/E)</span>
              <span className="metric-val">{report.valuation.pe_ratio ? `${report.valuation.pe_ratio}x` : "N/A"}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Price to Book (P/B)</span>
              <span className="metric-val">{report.valuation.pb_ratio ? `${report.valuation.pb_ratio}x` : "N/A"}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Dividend Yield</span>
              <span className="metric-val">{report.valuation.dividend_yield ? `${report.valuation.dividend_yield}%` : "0.0%"}</span>
            </div>
          </div>
        </div>

        {/* Risk Warning Panel */}
        <div className="card">
          <h2>🚨 Risk Indicators</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.5rem" }}>
            <div className="metric-row">
              <span className="metric-label">Daily Volatility (14-day ATR%)</span>
              <span className="metric-val">{report.risk.atr_pct}%</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Drawdown from 52-week High</span>
              <span className="metric-val" style={{ color: "var(--accent-rose)" }}>
                -{report.risk.drawdown_from_52w_high_pct}%
              </span>
            </div>
            <div className="metric-row" style={{ flexDirection: "column", gap: "0.5rem", borderBottom: "none" }}>
              <span className="metric-label">Active Warnings</span>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.25rem" }}>
                {report.risk.flags.length > 0 ? (
                  report.risk.flags.map((flag, idx) => (
                    <span key={idx} className="badge badge-bearish" style={{ fontWeight: "700" }}>
                      🚨 {flag}
                    </span>
                  ))
                ) : (
                  <span className="badge badge-bullish">🟢 NO WARNING FLAGS</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Index Inclusion Predictor section */}
      <div className="grid-cols-2" style={{ marginBottom: "2rem" }}>
        {/* Prediction probabilities card */}
        <div className="card">
          <h2>🔮 Index Inclusion Likelihood</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.25rem", marginBottom: "1.5rem" }}>
            Target Index: Nifty Momentum 50 (Calibrated Platt Ensemble)
          </p>

          {predLoading ? (
            <div style={{ padding: "2rem 0", textAlign: "center", color: "var(--text-secondary)" }}>
              Computing calibrated inclusion probabilities...
            </div>
          ) : predError ? (
            <div style={{ padding: "1.5rem 0", color: "var(--accent-rose)", fontSize: "0.9rem" }}>
              ⚠️ {predError}. Make sure the predictor server is running on port 8001.
            </div>
          ) : prediction ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span className="metric-label" style={{ fontWeight: "500" }}>3-Month Horizon</span>
                  <span className="metric-val" style={{ color: getProbColor(prediction.prob_3m) }}>
                    {(prediction.prob_3m * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px", overflow: "hidden" }}>
                  <div style={{ width: `${prediction.prob_3m * 100}%`, height: "100%", background: getProbColor(prediction.prob_3m), borderRadius: "4px", transition: "width 0.5s ease" }} />
                </div>
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span className="metric-label" style={{ fontWeight: "500" }}>6-Month Horizon</span>
                  <span className="metric-val" style={{ color: getProbColor(prediction.prob_6m) }}>
                    {(prediction.prob_6m * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px", overflow: "hidden" }}>
                  <div style={{ width: `${prediction.prob_6m * 100}%`, height: "100%", background: getProbColor(prediction.prob_6m), borderRadius: "4px", transition: "width 0.5s ease" }} />
                </div>
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span className="metric-label" style={{ fontWeight: "500" }}>12-Month Horizon</span>
                  <span className="metric-val" style={{ color: getProbColor(prediction.prob_12m) }}>
                    {(prediction.prob_12m * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px", overflow: "hidden" }}>
                  <div style={{ width: `${prediction.prob_12m * 100}%`, height: "100%", background: getProbColor(prediction.prob_12m), borderRadius: "4px", transition: "width 0.5s ease" }} />
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: "var(--text-secondary)" }}>No prediction data available.</div>
          )}
        </div>

        {/* Diagnostics & factors card */}
        <div className="card">
          <h2>📐 Model Diagnostics & Backtest</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1rem" }}>
            <div className="metric-row">
              <span className="metric-label">Model Architecture</span>
              <span className="metric-val">RandomForest + GradientBoosting</span>
            </div>
            {prediction && (
              <>
                <div className="metric-row">
                  <span className="metric-label">Walk-Forward Confidence</span>
                  <span className="metric-val" style={{ color: "var(--accent-emerald)" }}>High (75% Top-10 Precision)</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Average Log-Loss</span>
                  <span className="metric-val">{prediction.metrics.avg_log_loss.toFixed(4)}</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Top Predictive Factor</span>
                  <span className="metric-val">Previous Constituent Flag (45.2%)</span>
                </div>
              </>
            )}
            <div style={{ marginTop: "1rem", borderTop: "1px dashed var(--border-color)", paddingTop: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="metric-label">Validation details:</span>
              <a href="/backtest_report.md" target="_blank" rel="noopener noreferrer" className="btn-secondary" style={{ fontSize: "0.85rem", padding: "0.4rem 0.8rem", color: "var(--accent-purple)", borderColor: "var(--accent-purple)" }}>
                📄 View Backtest Report
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="disclaimer-alert">
        <strong>Risk Disclosure:</strong> The metrics shown above, including moving averages and composite momentum scores, are models based on historical datasets. Past performance does not guarantee future results. Tickers flagged with active warnings (e.g. <code>HIGH_DEBT</code> or <code>EARNINGS_DECLINE</code>) carry elevated positional risk. Verify structural metrics before taking swing positions.
      </div>
    </div>
  );
}

function getProbColor(prob: number): string {
  if (prob >= 0.7) return "var(--accent-emerald)";
  if (prob >= 0.4) return "var(--accent-amber)";
  return "var(--accent-rose)";
}

