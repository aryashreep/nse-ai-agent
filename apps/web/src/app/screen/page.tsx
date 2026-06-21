"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { screenMomentum, ScreenedStock } from "../../services/api";

export default function Screener() {
  const [stocks, setStocks] = useState<ScreenedStock[]>([]);
  const [sectorFilter, setSectorFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const SECTORS = [
    "ALL",
    "FMCG",
    "Financial Services",
    "Information Technology",
    "Energy",
    "Automobile"
  ];

  useEffect(() => {
    async function loadFilteredData() {
      try {
        setLoading(true);
        const filter = sectorFilter === "ALL" ? undefined : sectorFilter;
        const data = await screenMomentum(filter);
        setStocks(data);
      } catch (err: any) {
        setErrorMsg(`Screener failed to load: ${err.message || err}`);
      } finally {
        setLoading(false);
      }
    }
    loadFilteredData();
  }, [sectorFilter]);

  // Filter stocks on search query
  const filteredStocks = stocks.filter((s) => {
    const q = searchQuery.toLowerCase();
    return s.ticker.toLowerCase().includes(q) || s.name.toLowerCase().includes(q);
  });

  return (
    <div>
      <div className="dashboard-title-bar">
        <div>
          <h1 className="title-large">Momentum Screener</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Filter the Indian equity universe based on Relative Strength rankings and active risk flags.
          </p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: "220px" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.5rem", fontWeight: "600" }}>
              Filter by Sector
            </label>
            <select
              className="select-input"
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
            >
              {SECTORS.map((s, idx) => (
                <option key={idx} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div style={{ flex: 2, minWidth: "280px" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.5rem", fontWeight: "600" }}>
              Search Ticker or Company
            </label>
            <input
              type="text"
              className="input-text"
              placeholder="Search e.g. RELIANCE, Tata..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {errorMsg && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid var(--accent-rose)", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
          <p style={{ color: "var(--accent-rose)" }}>{errorMsg}</p>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div style={{ padding: "4rem 0", textAlign: "center", color: "var(--text-secondary)" }}>
            <h3>Running multi-factor scan on the database...</h3>
            <p style={{ marginTop: "0.5rem" }}>Retrieving technical states and updating relative indicators.</p>
          </div>
        ) : filteredStocks.length > 0 ? (
          <div className="table-container">
            <table className="stock-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Ticker</th>
                  <th>Sector</th>
                  <th>Trend</th>
                  <th>Momentum Score</th>
                  <th>RS Score</th>
                  <th>Risk Warnings</th>
                </tr>
              </thead>
              <tbody>
                {filteredStocks.map((stock, index) => {
                  const trendClass = stock.trend === "bullish" ? "badge-bullish" : stock.trend === "bearish" ? "badge-bearish" : "badge-neutral";
                  return (
                    <tr key={index}>
                      <td>{index + 1}</td>
                      <td>
                        <Link href={`/stock/${stock.ticker}`} style={{ fontWeight: "700", color: "white" }}>
                          {stock.ticker}
                        </Link>
                        <span style={{ display: "block", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                          {stock.name}
                        </span>
                      </td>
                      <td>{stock.sector}</td>
                      <td>
                        <span className={`badge ${trendClass}`}>{stock.trend.toUpperCase()}</span>
                      </td>
                      <td>
                        <strong style={{ color: "var(--accent-purple)" }}>{stock.momentum_score}/100</strong>
                      </td>
                      <td>{stock.rs_score}/100</td>
                      <td>
                        {stock.risk_flags.length > 0 ? (
                          <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
                            {stock.risk_flags.map((f, fi) => (
                              <span key={fi} className="badge badge-bearish" style={{ fontSize: "0.7rem", padding: "0.15rem 0.3rem" }}>
                                🚨 {f}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span style={{ color: "var(--accent-emerald)", fontSize: "0.8rem" }}>🟢 Low Risk</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
            No stocks matched the active search filters.
          </div>
        )}
      </div>
    </div>
  );
}
