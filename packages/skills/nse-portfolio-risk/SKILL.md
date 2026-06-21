---
name: nse-portfolio-risk
description: >-
  Portfolio risk analysis, FII/DII ownership tracking, and concentration risk
  scoring for NSE-listed Indian stocks. Use when the user asks to analyze
  portfolio risk, check FII/DII holdings, review promoter pledge, or assess
  institutional ownership structure.
compatibility: Requires Node.js 18+ for CLI. Python 3.9+ for advanced portfolio risk scoring.
metadata:
  author: aryashreep
  version: "1.0.0"
  npm_package: "@aryashreep/nse-ai-agent"
  github: "aryashreep/nse-ai-agent"
---

# NSE Portfolio Risk & FII/DII Analysis Skill

Specialized skill for institutional ownership analysis, portfolio risk scoring, and FII/DII flow tracking for Indian equity markets.

**Target users:** Portfolio managers, risk analysts, and fundamental investors tracking institutional money flow in NSE/BSE listed stocks.

---

## When to Use This Skill

- User asks to **analyze portfolio risk** (e.g., "What's the risk in my portfolio?")
- User asks about **FII/DII holdings** (e.g., "Show FII holdings in RELIANCE")
- User asks about **promoter pledge** (e.g., "Is there promoter pledge risk in TCS?")
- User asks for **ownership structure** (e.g., "Who owns ITC?")

---

## CLI Commands

```bash
nse-agent risk RELIANCE
nse-agent risk TCS --format json
nse-agent compare RELIANCE TCS HDFCBANK ITC INFY --format json
```

---

## MCP Tools

### fii_dii_flows

```python
fii_dii_flows("RELIANCE")
```

Returns: Promoter/FII/DII/Public holdings, pledge %, Institutional Quality Score (0-100).

### portfolio_review

```python
portfolio_review(["RELIANCE", "TCS", "HDFCBANK", "ITC", "INFY"])
```

Returns: Per-stock risk flags, portfolio concentration warnings, rebalancing suggestions.

---

## Risk Score Methodology (0-100)

| Component | Weight | Description |
|-----------|--------|-------------|
| Volatility | 30 pts | Annualized volatility |
| Max Drawdown | 20 pts | Peak-to-trough decline |
| Beta | 15 pts | Market sensitivity |
| VaR (95%) | 15 pts | Daily Value at Risk |
| Sharpe Ratio | 10 pts | Risk-adjusted return |
| Return Penalty | 10 pts | Underperformance |

| Score | Rating |
|-------|--------|
| 0-40 | Low Risk |
| 41-70 | Moderate Risk |
| 71-100 | High Risk |

---

## Ownership Quality Score (0-100)

| Component | Max Points |
|-----------|------------|
| Promoter Holding | 25 |
| FII Holding | 25 |
| DII Holding | 15 |
| Pledge Penalty | -20 |
| Low Institutional | -15 |

### Ownership Flags

| Flag | Condition | Severity |
|------|-----------|----------|
| HIGH_PROMOTER_PLEDGE | Pledge > 20% | Critical |
| LOW_FII_HOLDING | FII < 10% | Warning |
| STRONG_FII_PRESENCE | FII > 40% | Positive |
| STRONG_DII_SUPPORT | DII > 30% | Positive |

---

## Disclaimer

This tool is for educational and analytical purposes only. Consult a SEBI-registered investment advisor.
