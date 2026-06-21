# NSE AI Agent Platform

A production-grade, modular monorepo platform for quantitative equity research and swing-trend alignment analysis in the Indian stock market. The platform utilizes LangGraph multi-agent workflows, FastAPI microservices, an ML-based Index Inclusion Predictor, and a Next.js 14 web application Dashboard.

---

## 1. System Architecture & Workspaces

The repository is organized as a monorepo containing the following components:

### Applications
* **`apps/web` (Next.js 14 Web Dashboard):** Premium dark-themed dashboard built with vanilla CSS. Integrates real-time screeners, sector rotation quadrants, portfolio allocation safety calculators, and predictive index inclusion probability gauges.

### Packages
* **`packages/core` (Python Core Engine):** Exposes a FastAPI server (port `8000`) instrumented with Prometheus. Implements a multi-agent quantitative evaluation workflow in LangGraph, caching results in SQLite (`nse_platform.db`), and exposes stock metrics via a FastMCP server.
* **`packages/predictor` (ML Index Inclusion Predictor):** Independent ML package generating daily simulation histories, extracting ranking/strength features, and training calibrated ensemble models (`RandomForest` + `GradientBoosting` with Platt probability scaling) to forecast Nifty Momentum Index inclusions. Exposes an API on port `8001`.
* **`packages/cli` (TypeScript CLI Client):** A Node-based CLI compiled to JavaScript supporting direct analysis queries, sector screeners, and automatic HTTP fallbacks if the backend server is offline.

### Infrastructure & Caching
* **`infra/` (Observability):** Contains Prometheus scraping configs and Grafana configurations to monitor API query metrics, response latency, and agent step durations.
* **`data/` (SQLite Cache & Datasets):** Contains local caches and ML simulation data for training.

---

## 2. Walk-Forward Prediction Performance (Phase 5)

The index inclusion prediction module is trained using walk-forward cross-validation. Metrics derived from out-of-sample rebalancing evaluations:

| Metric | Score | Description |
| :--- | :--- | :--- |
| **Log-Loss** | `0.2997` | Calibrated prediction error (lower is better) |
| **Precision @ 5** | `95.00%` | Fraction of top 5 predictions included in the index |
| **Precision @ 10** | `75.00%` | Fraction of top 10 predictions included (exceeds 60% requirement) |
| **Recall @ 10** | `93.75%` | Fraction of actual constituents captured in top 10 forecasts |

---

## 3. Quick Start & Execution

### Installation

1. Install root Node dependencies:
   ```bash
   npm install
   ```

2. Setup python dependencies for the Core engine:
   ```bash
   pip install -r packages/core/requirements.txt
   ```

3. Setup python dependencies for the ML Predictor:
   ```bash
   pip install -r packages/predictor/requirements.txt
   ```

---

### Running the Platform Services

To boot the entire end-to-end stack, run the following commands in separate shell terminals:

#### Step 1: Start Core Analysis Engine (Port 8000)
Run from `packages/core/src/`:
```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

#### Step 2: Start ML Predictor Microservice (Port 8001)
Run from `packages/predictor/src/`:
```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8001
```

#### Step 3: Run Prometheus & Grafana Observability
Run from the root directory:
```bash
docker compose up -d
```

#### Step 4: Boot Web Dashboard (Port 3000)
Run from the root directory:
```bash
npm run dev --workspace=apps/web
```

---

### Running the command line interface (CLI)

Use the CLI to retrieve stock composite reports directly from the terminal. 

Build the CLI:
```bash
npm run build --workspace=packages/cli
```

Execute query:
```bash
nse-agent analyze TCS
```

---

## 4. SEBI Regulatory Compliance & Disclaimer

This platform is strictly for **educational and quantitative research purposes**. It does not output investment advice, financial target values, or explicit trade directives (e.g., buy/sell signals). 

Equity trading involves high structural risk. Users are advised to review raw structural metrics, consult a SEBI-registered Investment Advisor, and exercise due diligence. Past simulation performance is not indicative of future market returns.

---

## 5. License

MIT
