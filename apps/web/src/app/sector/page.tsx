"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { screenMomentum } from "../../services/api";

interface SectorStatus {
  name: string;
  score: number;
  tickersCount: number;
  leaders: string[];
}

export default function SectorRotation() {
  const [sectors, setSectors] = useState<SectorStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function computeSectors() {
      try {
        setLoading(true);
        // Load the full universe
        const data = await screenMomentum();
        
        // Group by sector
        const grouped: Record<string, { total: number; count: number; tickers: string[] }> = {};
        data.forEach((stock) => {
          if (!grouped[stock.sector]) {
            grouped[stock.sector] = { total: 0, count: 0, tickers: [] };
          }
          grouped[stock.sector].total += stock.momentum_score;
          grouped[stock.sector].count += 1;
          // Add top performing stocks in this sector to list
          if (grouped[stock.sector].tickers.length < 3) {
            grouped[stock.sector].tickers.push(stock.ticker);
          }
        });

        const list: SectorStatus[] = Object.keys(grouped).map((name) => ({
          name,
          score: Math.round(grouped[name].total / grouped[name].count),
          tickersCount: grouped[name].count,
          leaders: grouped[name].tickers
        }));
        
        // Sort by score descending
        setSectors(list.sort((a, b) => b.score - a.score));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    computeSectors();
  }, []);

  // Split into quadrants based on relative score
  const leading = sectors.filter((s) => s.score >= 60);
  const improving = sectors.filter((s) => s.score >= 45 && s.score < 60);
  const weakening = sectors.filter((s) => s.score >= 30 && s.score < 45);
  const lagging = sectors.filter((s) => s.score < 30);

  return (
    <div>
      <div className="dashboard-title-bar">
        <div>
          <h1 className="title-large">Sector Rotation Matrix</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Quad-based relative strength mappings of NSE industry segments.
          </p>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: "6rem", textAlign: "center", color: "var(--text-secondary)" }}>
          <h3>Scanning sectors averages...</h3>
        </div>
      ) : (
        <div className="grid-cols-2" style={{ gap: "2rem" }}>
          {/* Leading */}
          <div className="card" style={{ borderLeft: "4px solid var(--accent-emerald)" }}>
            <h2 style={{ color: "var(--accent-emerald)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>🔥 Leading Segment</span>
              <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "normal" }}>Score &ge; 60</span>
            </h2>
            <p style={{ color: "var(--text-secondary)", margin: "0.5rem 0 1.5rem 0", fontSize: "0.9rem" }}>
              High-velocity institutional inflows. Stocks in this quadrant exhibit strong upward trends.
            </p>
            {leading.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {leading.map((s, idx) => (
                  <div key={idx} className="metric-row">
                    <div>
                      <strong>{s.name}</strong>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                        Leaders: {s.leaders.join(", ")} ({s.tickersCount} stocks tracked)
                      </div>
                    </div>
                    <span className="badge badge-bullish" style={{ alignSelf: "center", minWidth: "50px", justifyContent: "center" }}>
                      {s.score}/100
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontStyle: "italic", fontSize: "0.85rem" }}>No sectors currently leading.</p>
            )}
          </div>

          {/* Improving */}
          <div className="card" style={{ borderLeft: "4px solid var(--accent-blue)" }}>
            <h2 style={{ color: "var(--accent-blue)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>📈 Improving Segment</span>
              <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "normal" }}>Score 45 - 59</span>
            </h2>
            <p style={{ color: "var(--text-secondary)", margin: "0.5rem 0 1.5rem 0", fontSize: "0.9rem" }}>
              Accumulation phase active. Momentum is accelerating, potential breakout candidates emerging.
            </p>
            {improving.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {improving.map((s, idx) => (
                  <div key={idx} className="metric-row">
                    <div>
                      <strong>{s.name}</strong>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                        Leaders: {s.leaders.join(", ")} ({s.tickersCount} stocks tracked)
                      </div>
                    </div>
                    <span className="badge badge-purple" style={{ alignSelf: "center", minWidth: "50px", justifyContent: "center" }}>
                      {s.score}/100
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontStyle: "italic", fontSize: "0.85rem" }}>No sectors currently improving.</p>
            )}
          </div>

          {/* Weakening */}
          <div className="card" style={{ borderLeft: "4px solid var(--accent-amber)" }}>
            <h2 style={{ color: "var(--accent-amber)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>🟡 Weakening Segment</span>
              <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "normal" }}>Score 30 - 44</span>
            </h2>
            <p style={{ color: "var(--text-secondary)", margin: "0.5rem 0 1.5rem 0", fontSize: "0.9rem" }}>
              Momentum fatigue. Institutional rotation observed; avoid fresh long exposure.
            </p>
            {weakening.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {weakening.map((s, idx) => (
                  <div key={idx} className="metric-row">
                    <div>
                      <strong>{s.name}</strong>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                        Leaders: {s.leaders.join(", ")} ({s.tickersCount} stocks tracked)
                      </div>
                    </div>
                    <span className="badge badge-neutral" style={{ alignSelf: "center", minWidth: "50px", justifyContent: "center" }}>
                      {s.score}/100
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontStyle: "italic", fontSize: "0.85rem" }}>No sectors currently weakening.</p>
            )}
          </div>

          {/* Lagging */}
          <div className="card" style={{ borderLeft: "4px solid var(--accent-rose)" }}>
            <h2 style={{ color: "var(--accent-rose)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>❄️ Lagging Segment</span>
              <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "normal" }}>Score &lt; 30</span>
            </h2>
            <p style={{ color: "var(--text-secondary)", margin: "0.5rem 0 1.5rem 0", fontSize: "0.9rem" }}>
              Distribution phase active. Relative strength is deeply underperforming. Avoid long positions.
            </p>
            {lagging.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {lagging.map((s, idx) => (
                  <div key={idx} className="metric-row">
                    <div>
                      <strong>{s.name}</strong>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                        Leaders: {s.leaders.join(", ")} ({s.tickersCount} stocks tracked)
                      </div>
                    </div>
                    <span className="badge badge-bearish" style={{ alignSelf: "center", minWidth: "50px", justifyContent: "center" }}>
                      {s.score}/100
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontStyle: "italic", fontSize: "0.85rem" }}>No sectors currently lagging.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
