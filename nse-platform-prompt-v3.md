# Build NSE AI Agent Platform

Act as a Principal Architect, AI Architect, Quantitative Researcher, Platform Engineer,
Open Source Maintainer, and Product Architect.

Build a production-grade open-source platform called:

**NSE AI Agent Platform**
Repository: `nse-ai-agent`

Mission: Create an Agentic AI platform that helps investors discover high-quality momentum
opportunities, perform institutional-grade stock research, and predict future momentum
index candidates.

Build incrementally through phases. Do not build everything at once.
Complete each phase's success criteria before starting the next.

---

# Architecture Principles

1. Single Monorepo
2. Modular Design — no package imports across phases that don't exist yet
3. API First — FastAPI is the single source of truth; CLI and MCP are thin clients
4. Agent First
5. MCP Compatible
6. Skills.sh Compatible
7. npm Publishable
8. Observability Built-In
9. Mock Data First — real providers are plug-ins, never assumptions
10. Production Ready

---

# Monorepo Structure

```
nse-ai-agent/
├── packages/
│   ├── skill/          # SKILL.md + docs (Skills.sh distribution)
│   ├── cli/            # Node.js + TypeScript CLI (npm distribution)
│   ├── core/           # Python + LangGraph agents + FastAPI
│   ├── mcp/            # TypeScript MCP server
│   └── predictor/      # Python ML project (Phase 5 only)
├── apps/
│   └── web/            # Next.js dashboard
├── data/
│   └── mock/           # Seed JSON files for MockProvider
├── docs/
├── examples/
├── infra/
│   └── docker-compose.yml
└── .github/
    └── workflows/
```

---

# Technology Decisions

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Agent Core     | Python 3.11 + LangGraph             |
| API Server     | FastAPI + Uvicorn                   |
| Memory         | Neo4j 5.x                          |
| CLI            | Node.js 20 + TypeScript             |
| MCP Server     | TypeScript                          |
| Frontend       | Next.js 14                          |
| Observability  | LangSmith (Phase 2), OpenTelemetry + Grafana (Phase 4) |
| Containers     | Docker + Docker Compose             |
| CI/CD          | GitHub Actions                      |

---

# Integration Architecture — Read This First

This is the most important section. Every phase must respect this contract.

```
                    ┌─────────────┐
                    │  FastAPI    │  ← Single source of truth
                    │  (Python)   │     localhost:8000
                    └──────┬──────┘
                           │ HTTP/JSON
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼─────┐  ┌───────▼──────┐  ┌─────▼──────┐
   │  CLI       │  │  MCP Server  │  │  Next.js   │
   │ (Node.js)  │  │ (TypeScript) │  │  (web)     │
   └────────────┘  └──────────────┘  └────────────┘
```

**Rule:** The CLI and MCP server are HTTP clients that call FastAPI.
They contain zero analysis logic.
All analysis, agent orchestration, and memory live in packages/core.

**Phase 1 exception:** Because FastAPI (packages/core) does not exist in Phase 1,
the CLI bundles a minimal self-contained TypeScript analysis module.
This module is replaced by FastAPI calls in Phase 2.
The CLI detects whether FastAPI is running:
- If reachable → call FastAPI
- If not reachable → use bundled fallback (Phase 1 mode only)

---

# Mock Data Contract — Canonical Schema

All packages must use these exact schemas.
Store seed files in data/mock/.

## MockProvider.get_stock(ticker: str) → StockSnapshot

```json
{
  "ticker": "ITC",
  "name": "ITC Limited",
  "sector": "FMCG",
  "industry": "Cigarettes",
  "exchange": "NSE",
  "isin": "INE154A01025",
  "price": 468.25,
  "open": 465.00,
  "high": 471.80,
  "low": 463.50,
  "prev_close": 464.90,
  "volume": 12450000,
  "market_cap_cr": 584200,
  "pe_ratio": 27.4,
  "pb_ratio": 6.8,
  "dividend_yield": 3.1,
  "52w_high": 528.00,
  "52w_low": 399.00,
  "as_of": "2026-06-19T15:30:00+05:30"
}
```

## MockProvider.get_history(ticker: str, days: int) → List[OHLCV]

```json
[
  {
    "date": "2026-06-19",
    "open": 465.00,
    "high": 471.80,
    "low": 463.50,
    "close": 468.25,
    "volume": 12450000,
    "delivery_pct": 48.2
  }
]
```

## MockProvider.get_fundamentals(ticker: str) → Fundamentals

```json
{
  "ticker": "ITC",
  "revenue_growth_yoy": 12.4,
  "profit_growth_yoy": 18.7,
  "roce": 31.2,
  "roe": 28.6,
  "debt_to_equity": 0.02,
  "free_cash_flow_cr": 14200,
  "earnings_acceleration": true,
  "promoter_holding_pct": 0.0,
  "promoter_pledge_pct": 0.0,
  "fii_holding_pct": 42.1,
  "dii_holding_pct": 35.8,
  "public_holding_pct": 22.1,
  "as_of_quarter": "Q4FY26"
}
```

## MarketDataProvider Interface (Python)

```python
from abc import ABC, abstractmethod
from typing import List
from models import StockSnapshot, OHLCV, Fundamentals

class MarketDataProvider(ABC):
    @abstractmethod
    def get_stock(self, ticker: str) -> StockSnapshot: ...

    @abstractmethod
    def get_history(self, ticker: str, days: int) -> List[OHLCV]: ...

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> Fundamentals: ...

# Phase 1 & 2 implementation
class MockProvider(MarketDataProvider):
    def __init__(self, data_dir: str = "data/mock"):
        # loads seed JSON files from data_dir
        ...

# Future implementations (do not build in Phase 1 or 2)
# class NSEProvider(MarketDataProvider): ...
# class VendorProvider(MarketDataProvider): ...
# class BrokerAPIProvider(MarketDataProvider): ...
```

Seed data must include at least 20 NSE tickers across 5 sectors.
Include at least one of each: strong momentum, weak momentum, high debt flag,
promoter pledge flag, earnings deterioration flag.

---

# Phase 1 — Skills.sh Skill + npm Package

## Goal

A working, installable, publishable CLI and skill.
The CLI uses a bundled TypeScript analysis module (no FastAPI dependency).

## Deliverables

`packages/skill/` and `packages/cli/`

## packages/skill/ Structure

```
packages/skill/
├── SKILL.md
├── README.md
├── examples/
│   ├── analyze-itc.md
│   ├── screen-momentum.md
│   └── compare-stocks.md
└── docs/
    ├── installation.md
    └── commands.md
```

## SKILL.md Purpose and Content

SKILL.md is an instruction file for AI agents. It tells an AI agent when and how
to use this skill. It does NOT contain analysis logic.

```markdown
---
name: nse-ai-agent
description: Use this skill to analyze NSE-listed Indian stocks, screen for
momentum opportunities, compare stocks, and generate research reports.
Trigger when the user asks about Indian stocks, NSE analysis, momentum
screening, sector rotation, or stock comparison. The skill invokes the
nse-agent CLI and interprets its structured JSON output.
---

# NSE Agentic Research Skill

## When to invoke this skill
- User asks to analyze a specific NSE stock (e.g. "analyze ITC" or "what's the momentum on HDFC?")
- User asks to screen for momentum stocks
- User asks to compare two or more NSE stocks
- User asks about sector rotation in Indian markets

## How to run

Install once:
npx skills add aryashreep/nse-ai-agent

Run:
npx nse-agent analyze <TICKER> --format json
npx nse-agent screen momentum --format json
npx nse-agent compare <TICKER1> <TICKER2> --format json

## Interpreting output
The CLI returns structured JSON. Parse the `momentum_score`, `quality_score`,
`risk_flags`, and `signals` fields to answer the user's question.
Do not present raw numbers — interpret them in plain language.
```

## CLI Commands (packages/cli/)

```bash
npx nse-agent analyze ITC
npx nse-agent analyze ITC --format json
npx nse-agent compare ITC HINDUNILVR
npx nse-agent screen momentum
npx nse-agent screen momentum --sector FMCG
```

## CLI Output Contract

`nse-agent analyze ITC` must return:

```json
{
  "ticker": "ITC",
  "as_of": "2026-06-19T15:30:00+05:30",
  "source": "mock",
  "technical": {
    "ema_21": 461.2,
    "ema_55": 448.7,
    "ema_200": 421.3,
    "price_vs_ema200_pct": 11.2,
    "trend": "bullish"
  },
  "momentum": {
    "rs_score": 78,
    "rs_velocity": 4.2,
    "volume_expansion": true,
    "atr_expansion": false,
    "momentum_score": 72
  },
  "risk": {
    "flags": [],
    "atr_pct": 1.8,
    "drawdown_from_52w_high_pct": 11.3
  },
  "valuation": {
    "pe_ratio": 27.4,
    "pb_ratio": 6.8,
    "dividend_yield": 3.1
  },
  "disclaimer": "For educational and research purposes only. Not investment advice."
}
```

## Bundled TypeScript Analysis Module

`packages/cli/src/analysis/` contains:

- `ema.ts` — EMA calculation (21, 55, 200)
- `momentum.ts` — RS score, RS velocity, volume expansion, ATR
- `risk.ts` — flag detection (high debt, pledge, drawdown)
- `valuation.ts` — snapshot formatting

These are self-contained. They accept OHLCV arrays and Fundamentals objects.
They do not call FastAPI. They will be deprecated in Phase 2 when FastAPI
is available, but the code remains as fallback.

## Phase 1 Success Criteria

- [ ] `npx nse-agent analyze ITC` returns valid JSON in under 3 seconds
- [ ] `npx nse-agent screen momentum` returns at least 5 ranked tickers
- [ ] `npx skills add aryashreep/nse-ai-agent` installs without errors
- [ ] Package publishes to npm as `@aryashreep/nse-ai-agent` without errors
- [ ] All 20 mock tickers return results without crashing
- [ ] Disclaimer is present in every output

---

# Phase 2 — Agent Core

## Goal

Python + LangGraph agents behind FastAPI. CLI switches to calling FastAPI.
LangSmith tracing enabled from day one.

## Deliverables

`packages/core/`

## FastAPI Endpoints (minimum)

```
POST /analyze          body: { ticker, options? }
POST /screen           body: { strategy, filters? }
POST /compare          body: { tickers: [str] }
GET  /health
```

## Neo4j Graph Schema

```
Nodes:
  (:Stock { ticker, name, sector, last_updated })
  (:AgentRun { run_id, agent_name, timestamp, duration_ms, success })
  (:Score { type, value, confidence, computed_at })
  (:RiskFlag { type, severity, description })
  (:Sector { name, rotation_score })

Relationships:
  (:Stock)-[:BELONGS_TO]->(:Sector)
  (:AgentRun)-[:ANALYZED]->(:Stock)
  (:AgentRun)-[:PRODUCED]->(:Score)
  (:AgentRun)-[:RAISED]->(:RiskFlag)
  (:Stock)-[:HAS_SCORE]->(:Score)
```

## Multi-Agent Communication Model

A **Supervisor Agent** orchestrates a sequential pipeline per analysis request:

```
Request
  │
  ▼
SupervisorAgent
  │
  ├──► MarketScannerAgent   → StockSnapshot + OHLCV
  │         (output fed as input to next agents)
  │
  ├──► MomentumAgent        → MomentumScore
  │
  ├──► FundamentalAgent     → QualityScore
  │
  ├──► OwnershipAgent       → OwnershipScore
  │
  └──► SectorRotationAgent  → SectorContext
          │
          ▼
      SupervisorAgent aggregates all scores
          │
          ▼
      Writes to Neo4j
          │
          ▼
      Returns CompositeReport
```

Agents are sequential, not parallel, in Phase 2.
Parallel execution is a Phase 4 optimization.
Each agent receives the full context object from the previous agent's output.

## Agent Output Schemas

### MomentumAgent → MomentumScore

```python
class MomentumScore(BaseModel):
    ticker: str
    ema_21: float
    ema_55: float
    ema_200: float
    rs_score: float          # 0-100, relative to Nifty 500 universe
    rs_velocity: float       # rate of change of RS score
    volume_expansion: bool
    atr_expansion: bool
    trend_persistence: int   # consecutive days above EMA 200
    score: float             # 0-100 composite
    confidence: float        # 0-1
    breakout_signal: bool
    trend_strength: str      # "strong" | "moderate" | "weak" | "none"
```

### FundamentalAgent → QualityScore

```python
class QualityScore(BaseModel):
    ticker: str
    revenue_growth_yoy: float
    profit_growth_yoy: float
    roce: float
    roe: float
    debt_to_equity: float
    free_cash_flow_cr: float
    earnings_acceleration: bool
    score: float             # 0-100 composite
    confidence: float        # 0-1
```

### OwnershipAgent → OwnershipScore

```python
class OwnershipScore(BaseModel):
    ticker: str
    promoter_holding_pct: float
    promoter_pledge_pct: float
    fii_holding_pct: float
    dii_holding_pct: float
    fii_trend: str           # "increasing" | "decreasing" | "stable"
    dii_trend: str
    float_quality: str       # "institutional" | "retail_heavy" | "concentrated"
    score: float             # 0-100 composite
    confidence: float        # 0-1
```

## LangSmith Tracing (Phase 2)

Wrap every LangGraph graph execution with LangSmith.
Every agent run must emit:

```python
{
    "agent_name": str,
    "ticker": str,
    "run_id": str,
    "duration_ms": int,
    "llm_calls": int,
    "token_usage": { "input": int, "output": int },
    "cost_usd": float,
    "decision_trace": [str],   # list of reasoning steps
    "errors": [str]
}
```

## CLI Integration (Phase 2 update)

Update CLI to detect FastAPI:

```typescript
async function getClient(): Promise<AnalysisClient> {
  const isApiUp = await ping("http://localhost:8000/health");
  if (isApiUp) return new FastAPIClient("http://localhost:8000");
  console.warn("⚠ FastAPI not running — using local fallback (mock data only)");
  return new LocalClient(); // Phase 1 bundled module
}
```

## docker-compose.yml (Phase 2)

```yaml
services:
  api:
    build: ./packages/core
    ports: ["8000:8000"]
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
    depends_on: [neo4j]

  neo4j:
    image: neo4j:5
    ports: ["7474:7474", "7687:7687"]
    environment:
      - NEO4J_AUTH=neo4j/devpassword
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
```

## Phase 2 Success Criteria

- [ ] `docker-compose up` starts API + Neo4j without errors
- [ ] `POST /analyze` with ticker "ITC" returns CompositeReport in under 10 seconds
- [ ] All 6 agents execute and write results to Neo4j
- [ ] LangSmith dashboard shows agent traces with token usage
- [ ] CLI auto-detects FastAPI and switches to API mode
- [ ] Risk flags (high debt, pledge) correctly identified from mock data

---

# Phase 3 — MCP Server

## Goal

TypeScript MCP server that wraps FastAPI, making all agents accessible to
Claude Code, Cursor, OpenAI Agents, Gemini CLI, and Codex.

## Deliverables

`packages/mcp/`

## Architecture

```
AI Agent (Claude Code / Cursor / etc.)
    │
    │ MCP protocol
    ▼
packages/mcp (TypeScript MCP server)
    │
    │ HTTP → localhost:8000
    ▼
packages/core (FastAPI)
    │
    ▼
LangGraph Agents + Neo4j
```

The MCP server is a thin HTTP-to-MCP adapter. It contains zero analysis logic.

## MCP Tools to Expose

```typescript
tools: [
  {
    name: "analyze_stock",
    description: "Run full multi-agent analysis on an NSE stock ticker",
    inputSchema: { ticker: string, options?: { include_sector: boolean } }
  },
  {
    name: "screen_momentum",
    description: "Screen NSE stocks for momentum opportunities",
    inputSchema: { sector?: string, min_rs_score?: number, limit?: number }
  },
  {
    name: "compare_stocks",
    description: "Compare two or more NSE stocks across all agent scores",
    inputSchema: { tickers: string[] }
  },
  {
    name: "sector_rotation",
    description: "Identify leading, improving, and weakening sectors",
    inputSchema: { universe?: string }
  },
  {
    name: "portfolio_review",
    description: "Review a portfolio of NSE stocks and flag risks",
    inputSchema: { tickers: string[], weights?: Record<string, number> }
  }
]
```

## Phase 3 Success Criteria

- [ ] MCP server registers all 5 tools without errors
- [ ] `analyze_stock({ ticker: "ITC" })` called from Claude Code returns structured result
- [ ] MCP server listed in Claude Code's available tools after config
- [ ] All tools pass through to FastAPI correctly (no silent failures)
- [ ] Error responses from FastAPI are surfaced cleanly to the AI agent

---

# Phase 4 — Web Platform

## Goal

Next.js dashboard consuming FastAPI directly.

## Deliverables

`apps/web/`

## Key Pages

```
/                  → Dashboard: momentum rankings, sector heat map
/stock/[ticker]    → Deep analysis page (all agent scores)
/screen            → Momentum screener with filters
/sector            → Sector rotation view
/watchlist         → User watchlists (localStorage for v1)
/portfolio         → Portfolio risk review
```

## API Integration

Next.js calls FastAPI directly via environment variable:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

No BFF layer in Phase 4. Add one in Phase 5 if needed.

## Observability Addition (Phase 4)

Add OpenTelemetry to FastAPI.
Add Grafana dashboard (via docker-compose) showing:
- Agent execution time per ticker
- API request rate
- Neo4j query latency
- Error rate

```yaml
# add to docker-compose.yml
  grafana:
    image: grafana/grafana
    ports: ["3001:3000"]
  otel-collector:
    image: otel/opentelemetry-collector
```

## Phase 4 Success Criteria

- [ ] Dashboard renders momentum rankings for all 20 mock tickers
- [ ] Stock detail page shows all agent scores with visual indicators
- [ ] Screener filters by sector and RS score correctly
- [ ] Grafana dashboard shows agent execution times
- [ ] All pages load in under 2 seconds (mock data, local)

---

# Phase 5 — Index Inclusion Predictor

## Goal

A standalone ML project that predicts Nifty Momentum Index reconstitution.
This is NOT an agent. Do not use LangGraph here.

## Deliverables

`packages/predictor/`

## Why This Is Separate

Index inclusion prediction requires:
- Historical index constituent data (labeled dataset)
- Factor data going back multiple years
- A backtesting framework to validate predictions
- Model training and evaluation pipelines

None of this exists in the agent core. Building it as an "agent" would produce
nothing that actually works. It is a data science project first.

## Data Requirements (must be sourced before modeling begins)

```
data/predictor/
├── constituents/           # Historical index composition (JSON per index per date)
│   ├── nifty_500_momentum_50/
│   ├── nifty_200_momentum_30/
│   └── nifty_midcap150_momentum_50/
├── prices/                 # Daily OHLCV for full NSE universe, 5 years minimum
├── fundamentals/           # Quarterly fundamentals per stock
└── factors/                # Pre-computed factor scores per stock per date
```

Do not start modeling until this data exists and is validated.

## Feature Engineering

Compute per stock, per reconstitution date:

```python
features = {
    "rs_12m": float,              # 12-month relative strength vs Nifty 500
    "rs_6m": float,               # 6-month relative strength
    "rs_3m": float,               # 3-month relative strength
    "rs_momentum_score": float,   # Index methodology approximation
    "volume_ratio_3m": float,     # avg volume vs 6-month avg
    "ema_200_distance_pct": float,
    "roce": float,
    "roe": float,
    "debt_to_equity": float,
    "market_cap_rank": int,       # rank within eligible universe
    "current_constituent": bool,  # is it in the index right now?
    "was_added_prev": bool,       # was it added in previous reconstitution?
}
```

## Models

Train three ensemble models:
- XGBoost
- LightGBM
- CatBoost

Ensemble via soft voting. Calibrate probabilities with Platt scaling.

## Backtesting Framework

Walk-forward validation only. No look-ahead bias.
For each historical reconstitution event:
- Train on data before that date
- Predict for that date
- Compare predictions to actual additions

## Output Schema

```python
class IndexInclusionPrediction(BaseModel):
    ticker: str
    index: str
    prob_3m: float        # 0-1
    prob_6m: float        # 0-1
    prob_12m: float       # 0-1
    confidence: float     # 0-1
    key_factors: list[str]
    model_version: str
    as_of: str
```

## Minimum Viable Accuracy

Before exposing predictions in any UI:
- Precision at top-10 predictions > 60% on out-of-sample reconstitution events
- Documented backtesting results must exist

## Phase 5 Success Criteria

- [ ] Historical constituent data collected and validated for at least 3 years
- [ ] Feature pipeline runs without data leakage
- [ ] All three models trained and evaluated
- [ ] Walk-forward backtest documented with precision/recall per index
- [ ] `packages/predictor` exposes a FastAPI endpoint `/predict-inclusion`
- [ ] Predictions integrated into web dashboard (Phase 4 page update)

---

# Risk Flags — Universal

Every agent pipeline must detect and surface these flags.
A flagged stock must include the flag in the output even if its composite score is high.

```python
RISK_FLAGS = {
    "HIGH_DEBT":           "Debt to Equity > 1.5",
    "PROMOTER_PLEDGE":     "Promoter pledge > 20% of holding",
    "EARNINGS_DECLINE":    "Profit growth negative YoY",
    "DISTRIBUTION":        "Volume expanding on down days > 3 consecutive",
    "SECTOR_WEAKNESS":     "Sector RS score < 30",
    "VOLATILITY_EXPANSION":"ATR expanding > 30% above 20-day average",
    "LOW_FLOAT":           "Public float < 15%",
    "FII_EXIT":            "FII holding declining > 3 consecutive quarters"
}
```

---

# CI/CD (.github/workflows/)

## ci.yml — runs on every PR

```yaml
jobs:
  test-cli:      # npm test in packages/cli
  test-core:     # pytest in packages/core
  lint:          # eslint + black + ruff
  build-docker:  # docker compose build (no push)
```

## publish-skill.yml — runs on tag v*

```yaml
jobs:
  publish-npm:   # npm publish packages/cli
  validate-skill: # verify SKILL.md structure
```

---

# Compliance

Every output — CLI, MCP, web, API — must include:

```
"disclaimer": "This platform provides educational and research information only.
It does not provide personalized investment advice. Past performance does not
guarantee future results. Consult a SEBI-registered investment advisor before
making investment decisions."
```

Design for future SEBI Research Analyst (RA) compliance:
- Never use the word "recommend" in output
- Never state a target price as a fact — only as a model output with confidence
- Log all predictions with timestamps for audit trail

---

# Final Vision

The completed platform functions as an Agentic AI Research Platform
for Indian Equities, capable of:

- Autonomous market scanning across the NSE universe
- Multi-agent research: momentum + fundamentals + ownership + sector
- MCP integration with every major AI coding agent
- Skills.sh distribution for AI-native consumption
- npm distribution for developer adoption
- Index inclusion prediction backed by a real backtesting framework

**North Star:** Become the Bloomberg Terminal for Momentum Investors,
powered by Agentic AI, built in the open.
