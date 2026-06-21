"use client";

import { useState } from "react";
import { compareStocks } from "../../services/api";

interface HoldingInput {
  ticker: string;
  weight: number;
}

export default function PortfolioReview() {
  const [holdings, setHoldings] = useState<HoldingInput[]>([
    { ticker: "RELIANCE", weight: 30 },
    { ticker: "TCS", weight: 25 },
    { ticker: "HDFCBANK", weight: 25 },
    { ticker: "ITC", weight: 20 }
  ]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const updateHolding = (index: number, key: keyof HoldingInput, val: any) => {
    const updated = [...holdings];
    if (key === "weight") {
      updated[index].weight = Number(val);
    } else {
      updated[index].ticker = String(val).toUpperCase().trim();
    }
    setHoldings(updated);
  };

  const addHolding = () => {
    setHoldings([...holdings, { ticker: "", weight: 0 }]);
  };

  const removeHolding = (index: number) => {
    setHoldings(holdings.filter((_, i) => i !== index));
  };

  const runAudit = async () => {
    setErrorMsg("");
    setResults(null);
    
    // Validate weights sum to 100
    const totalWeight = holdings.reduce((sum, h) => sum + h.weight, 0);
    if (Math.abs(totalWeight - 100) > 0.01) {
      setErrorMsg(`⚠️ Total weight allocation must sum to exactly 100%. Currently it is: ${totalWeight}%`);
      return;
    }

    const tickers = holdings.map((h) => h.ticker).filter(Boolean);
    if (tickers.length === 0) {
      setErrorMsg("⚠️ Please enter at least one valid ticker symbol.");
      return;
    }

    try {
      setLoading(true);
      const data = await compareStocks(tickers);
      
      // Calculate weighted statistics
      let weightedBeta = 0;
      let weightedDrawdown = 0;
      let weightedAtr = 0;
      let overallScore = 0;
      let activeWarnings: string[] = [];
      const sectorWeights: Record<string, number> = {};
      const stockWeights: Record<string, number> = {};

      data.forEach((stock, idx) => {
        if (stock.error) return;
        const weightFraction = holdings[idx].weight / 100;
        
        // Define beta based on sector
        const sector = stock.sector || "FMCG";
        let beta = 1.0;
        if (sector === "FMCG") beta = 0.75;
        if (sector === "Financial Services") beta = 1.15;
        if (sector === "Information Technology") beta = 0.95;
        if (sector === "Energy") beta = 0.9;
        if (sector === "Automobile") beta = 1.25;

        weightedBeta += beta * weightFraction;
        weightedDrawdown += stock.risk.drawdown_from_52w_high_pct * weightFraction;
        weightedAtr += stock.risk.atr_pct * weightFraction;
        overallScore += stock.momentum.momentum_score * weightFraction;
        
        // Collate warnings
        stock.risk.flags.forEach((f: string) => {
          if (!activeWarnings.includes(f)) {
            activeWarnings.push(f);
          }
        });

        // Concentration mappings
        sectorWeights[sector] = (sectorWeights[sector] || 0) + holdings[idx].weight;
        stockWeights[stock.ticker] = (stockWeights[stock.ticker] || 0) + holdings[idx].weight;
      });

      // Constraints validations
      const sectorViolations = Object.keys(sectorWeights).filter((s) => sectorWeights[s] > 40);
      const stockViolations = Object.keys(stockWeights).filter((s) => stockWeights[s] > 20);

      setResults({
        beta: roundDec(weightedBeta, 2),
        drawdown: roundDec(weightedDrawdown, 1),
        volatility: roundDec(weightedAtr, 2),
        score: roundDec(overallScore, 1),
        warnings: activeWarnings,
        sectorWeights,
        stockWeights,
        sectorViolations,
        stockViolations
      });
    } catch (err: any) {
      setErrorMsg(`Portfolio audit failed: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const roundDec = (val: number, dec: number) => {
    return Math.round(val * Math.pow(10, dec)) / Math.pow(10, dec);
  };

  return (
    <div>
      <div className="dashboard-title-bar">
        <div>
          <h1 className="title-large">Portfolio Risk Review</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Audit sector concentrations, beta ratios, and active risk flag exposures for custom holdings.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid var(--accent-rose)", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
          <p style={{ color: "var(--accent-rose)" }}>{errorMsg}</p>
        </div>
      )}

      <div className="grid-cols-3" style={{ gap: "2rem" }}>
        {/* Holdings input panel */}
        <div className="card" style={{ gridColumn: "span 2" }}>
          <h2>Holdings & Allocation Weights</h2>
          <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {holdings.map((h, index) => (
              <div key={index} style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                <div style={{ flex: 2 }}>
                  <input
                    type="text"
                    className="input-text"
                    placeholder="Ticker e.g. TCS"
                    value={h.ticker}
                    onChange={(e) => updateHolding(index, "ticker", e.target.value)}
                  />
                </div>
                <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <input
                    type="number"
                    className="input-text"
                    placeholder="Weight %"
                    value={h.weight || ""}
                    onChange={(e) => updateHolding(index, "weight", e.target.value)}
                  />
                  <span>%</span>
                </div>
                <button
                  className="btn-secondary"
                  style={{ color: "var(--accent-rose)", borderColor: "rgba(239,68,68,0.2)", padding: "0.5rem 0.75rem" }}
                  onClick={() => removeHolding(index)}
                >
                  Remove
                </button>
              </div>
            ))}
            
            <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
              <button className="btn-secondary" onClick={addHolding}>+ Add Stock</button>
              <button className="btn-primary" onClick={runAudit} disabled={loading}>
                {loading ? "Analyzing Holdings..." : "Run Portfolio Audit"}
              </button>
            </div>
          </div>
        </div>

        {/* Results summary panel */}
        <div className="card">
          <h2>Risk Metrics Scorecard</h2>
          {results ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.5rem" }}>
              <div className="metric-row">
                <span className="metric-label">Weighted Portfolio Beta</span>
                <span className="metric-val" style={{ color: results.beta > 1.0 ? "var(--accent-amber)" : "var(--accent-emerald)" }}>
                  {results.beta}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Avg Portfolio Drawdown</span>
                <span className="metric-val" style={{ color: "var(--accent-rose)" }}>-{results.drawdown}%</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Avg Daily Volatility (ATR)</span>
                <span className="metric-val">{results.volatility}%</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Composite Momentum Score</span>
                <span className="metric-val" style={{ color: "var(--accent-purple)", fontSize: "1.1rem" }}>
                  {results.score}/100
                </span>
              </div>
            </div>
          ) : (
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", fontStyle: "italic", marginTop: "1.5rem" }}>
              Configure your holdings on the left and run the audit to review statistics.
            </p>
          )}
        </div>
      </div>

      {results && (
        <div className="grid-cols-2" style={{ gap: "2rem", marginTop: "2rem" }}>
          {/* Concentration Warnings */}
          <div className="card">
            <h2>Concentration Compliance Audit</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1rem" }}>
              <div className="metric-row" style={{ borderBottom: "none" }}>
                <span>Stock Cap Rules (&le; 20% per stock):</span>
                <span>
                  {results.stockViolations.length > 0 ? (
                    <span style={{ color: "var(--accent-rose)", fontWeight: "bold" }}>
                      ⚠️ Violation ({results.stockViolations.join(", ")})
                    </span>
                  ) : (
                    <span style={{ color: "var(--accent-emerald)" }}>✅ Passed</span>
                  )}
                </span>
              </div>
              <div className="metric-row" style={{ borderBottom: "none" }}>
                <span>Sector Cap Rules (&le; 40% per sector):</span>
                <span>
                  {results.sectorViolations.length > 0 ? (
                    <span style={{ color: "var(--accent-rose)", fontWeight: "bold" }}>
                      ⚠️ Violation ({results.sectorViolations.join(", ")})
                    </span>
                  ) : (
                    <span style={{ color: "var(--accent-emerald)" }}>✅ Passed</span>
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* Active Risk flags in Portfolio */}
          <div className="card">
            <h2>Exposure Risk Flags</h2>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "1rem" }}>
              {results.warnings.length > 0 ? (
                results.warnings.map((w: string, idx: number) => (
                  <span key={idx} className="badge badge-bearish" style={{ fontWeight: "700" }}>
                    🚨 {w}
                  </span>
                ))
              ) : (
                <span className="badge badge-bullish">🟢 NO ACTIVE WARNING FLAGS IN PORTFOLIO</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
