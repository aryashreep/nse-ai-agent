---
name: nse-backtesting
description: >-
  Backtest trading strategies on NSE-listed Indian stocks using historical data.
  Use when the user asks to backtest a strategy, test EMA crossover, RSI mean
  reversion, breakout retest, or EMA pullback on Indian stocks.
compatibility: Requires Node.js 18+ for CLI. Python 3.9+ with pandas, numpy for full backtest engine.
metadata:
  author: aryashreep
  version: "1.0.0"
  npm_package: "@aryashreep/nse-ai-agent"
  github: "aryashreep/nse-ai-agent"
---

# NSE Strategy Backtesting Skill

Specialized skill for backtesting trading strategies on NSE-listed Indian stocks using historical OHLCV data with realistic trade simulation.

**Target users:** Systematic traders, quant researchers, and strategy developers testing approaches on Indian equity markets.

---

## When to Use This Skill

- User asks to **backtest a strategy** (e.g., "Backtest EMA crossover on TCS")
- User asks about **strategy performance** (e.g., "How does RSI mean reversion work on INFY?")
- User asks to **compare strategies** (e.g., "Which strategy works best on HDFCBANK?")

---

## CLI Commands

```bash
nse-agent backtest TCS --strategy triple-ema-crossover
nse-agent backtest RELIANCE --strategy rsi-mean-reversion --capital 500000
nse-agent backtest INFY --strategy breakout-retest --format json
```

### Available Strategies

| Strategy | Command | Description | Best For |
|----------|---------|-------------|----------|
| Triple EMA Crossover | triple-ema-crossover | 9/21/55 EMA crossover with volume filter | Trending markets |
| RSI Mean Reversion | rsi-mean-reversion | Buy RSI < 30, sell RSI > 70 with EMA filter | Range-bound markets |
| Breakout Retest | breakout-retest | Buy on breakout retest with volume confirmation | Consolidation breakouts |
| EMA Pullback | ema-pullback | Buy on pullback to 21 EMA in uptrend | Trending pullbacks |

---

## MCP Tool: backtest_strategy

```python
backtest_strategy(ticker="TCS", strategy="triple-ema-crossover", capital=1000000)
```

---

## Output Metrics

| Metric | Description |
|--------|-------------|
| Total Return | Absolute return over the backtest period |
| CAGR | Compound Annual Growth Rate |
| Max Drawdown | Largest peak-to-trough decline |
| Sharpe Ratio | Risk-adjusted return (annualized) |
| Win Rate | Percentage of winning trades |
| Profit Factor | Gross profit / Gross loss |
| Total Trades | Number of round-trip trades |
| Risk:Reward | Average win / Average loss |

---

## Risk Management in Backtests

1. **ATR-based stop loss**: 2x ATR from entry price
2. **Position sizing**: Risk 1% of capital per trade
3. **Commission**: 0.1% per trade (entry + exit)
4. **No leverage**: Cash-only simulation

---

## Disclaimer

Backtest results do not guarantee future performance. This tool is for educational and research purposes only.
