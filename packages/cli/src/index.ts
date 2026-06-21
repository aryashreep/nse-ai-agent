import { Command } from "commander";
import axios from "axios";
import { execSync } from "child_process";
import * as path from "path";

const API_URL = process.env.NSE_AGENT_API_URL || "http://127.0.0.1:8000";
const program = new Command();
const pythonAnalyzerPath = path.resolve(__dirname, "../../core/src/local_analyzer.py");
const mcpServerPath = path.resolve(__dirname, "../../core/src/mcp_server.py");

async function isApiRunning(): Promise<boolean> {
  try {
    const r = await axios.get(`${API_URL}/health`, { timeout: 800 });
    return r.status === 200 && r.data.status === "healthy";
  } catch { return false; }
}

function runPythonFallback(args: string[]): any {
  try {
    return JSON.parse(
      execSync(`python "${pythonAnalyzerPath}" ${args.join(" ")}`, {
        encoding: "utf-8",
        stdio: ["ignore", "pipe", "pipe"],
      }).trim()
    );
  } catch (e: any) {
    return { error: "LocalExecutionError", message: e.message };
  }
}

function printDisclaimer(d: string) {
  console.log("\n---");
  console.log(`DISCLAIMER: ${d}`);
  console.log("---\n");
}

program.name("nse-agent").description("NSE AI Agent - agentic analysis, screening, and reporting for Indian stocks").version("1.1.0");

// analyze
program.command("analyze <ticker>")
  .description("Perform full analysis on an NSE stock ticker")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (ticker, options) => {
    let result: any;
    const apiUp = await isApiRunning();
    if (apiUp) {
      try {
        const r = await axios.post(`${API_URL}/analyze`, { ticker });
        result = r.data;
      } catch (error: any) {
        result = error.response?.status === 404
          ? { error: "NotFoundError", message: `Ticker ${ticker} not found.` }
          : { error: "ApiError", message: error.message };
      }
    } else {
      result = runPythonFallback(["analyze", ticker]);
    }
    if (options.format === "json") { console.log(JSON.stringify(result, null, 2)); return; }
    if (result.error) { console.error(`ERROR: [${result.error}] | Cause: ${result.message}`); return; }
    console.log(`\n=== NSE AGENTIC RESEARCH: ${result.ticker} (${result.as_of}) ===`);
    console.log(`Source Provider: ${result.source.toUpperCase()}`);
    console.log("--------------------------------------------------------------------------------");
    const tc = result.technical.trend === "bullish" ? "[32m▲[0m" : result.technical.trend === "bearish" ? "[31m▼[0m" : "[33m━[0m";
    console.log("Technical Snapshot:");
    console.log(`  Trend:           ${tc} ${result.technical.trend.toUpperCase()}`);
    console.log(`  EMA 21 / 55:     ₹${result.technical.ema_21} / ₹${result.technical.ema_55}`);
    console.log(`  EMA 200:         ₹${result.technical.ema_200}`);
    console.log(`  vs EMA 200:      ${result.technical.price_vs_ema200_pct > 0 ? "+" : ""}${result.technical.price_vs_ema200_pct}%`);
    console.log("\nMomentum Profile:");
    console.log(`  Composite Score: ${result.momentum.momentum_score}/100`);
    console.log(`  RS Score:        ${result.momentum.rs_score}/100`);
    console.log(`  RS Velocity:     ${result.momentum.rs_velocity > 0 ? "+" : ""}${result.momentum.rs_velocity}`);
    console.log(`  Volume Surge:    ${result.momentum.volume_expansion ? "YES" : "NO"}`);
    console.log(`  ATR Expansion:   ${result.momentum.atr_expansion ? "YES" : "NO"}`);
    console.log("\nValuation Multiples:");
    console.log(`  P/E Ratio:       ${result.valuation.pe_ratio !== null ? result.valuation.pe_ratio + "x" : "N/A"}`);
    console.log(`  P/B Ratio:       ${result.valuation.pb_ratio !== null ? result.valuation.pb_ratio + "x" : "N/A"}`);
    console.log(`  Dividend Yield:  ${result.valuation.dividend_yield !== null ? result.valuation.dividend_yield + "%" : "N/A"}`);
    console.log("\nRisk Assessment:");
    console.log(`  Daily Vol (ATR): ${result.risk.atr_pct}%`);
    console.log(`  Drawdown (52w):  -${result.risk.drawdown_from_52w_high_pct}%`);
    if (result.risk.flags && result.risk.flags.length > 0) {
      console.log(`  Risk Flags:      ${result.risk.flags.join(", ")}`);
    } else {
      console.log(`  Risk Flags:      NONE`);
    }
    printDisclaimer(result.disclaimer);
  });

// screen
program.command("screen [strategy]")
  .description("Screen stocks for momentum setups")
  .option("--sector <sector>", "Filter results by sector")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (strategy = "momentum", options) => {
    let result: any;
    const apiUp = await isApiRunning();
    if (apiUp) {
      try {
        const r = await axios.post(`${API_URL}/screen`, { strategy, sector: options.sector });
        result = r.data;
      } catch (error: any) {
        result = { error: "ApiError", message: error.message };
      }
    } else {
      const pyArgs = ["screen", strategy];
      if (options.sector) pyArgs.push("--sector", `"${options.sector}"`);
      result = runPythonFallback(pyArgs);
    }
    if (options.format === "json") { console.log(JSON.stringify(result, null, 2)); return; }
    if (result.error) { console.error(`ERROR: [${result.error}] | Cause: ${result.message}`); return; }
    console.log("\n=== MOMENTUM SCREENER RESULTS (Universe: 20 Tickers) ===");
    if (options.sector) console.log(`Sector Filter: ${options.sector}`);
    console.log("--------------------------------------------------------------------------------");
    console.log(String("Rank").padEnd(5) + String("Ticker").padEnd(12) + String("Sector").padEnd(20) + String("Trend").padEnd(10) + String("Mom. Score").padEnd(12) + "Risk Flags");
    console.log("--------------------------------------------------------------------------------");
    result.forEach((stock: any, index: number) => {
      const tc = stock.trend === "bullish" ? "[32m▲[0m" : stock.trend === "bearish" ? "[31m▼[0m" : "[33m━[0m";
      const flags = stock.risk_flags.length > 0 ? stock.risk_flags.join(", ") : "None";
      console.log(String(index + 1).padEnd(5) + String(stock.ticker).padEnd(12) + String(stock.sector).padEnd(20) + tc.padEnd(16) + String(stock.momentum_score).padEnd(12) + flags);
    });
    console.log("--------------------------------------------------------------------------------");
    printDisclaimer("This platform provides educational and research information only. Consult a SEBI-registered advisor before trading.");
  });

// compare
program.command("compare <tickers...>")
  .description("Compare multiple NSE stock tickers side-by-side")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (tickers, options) => {
    let result: any;
    const apiUp = await isApiRunning();
    if (apiUp) {
      try {
        const r = await axios.post(`${API_URL}/compare`, { tickers });
        result = r.data;
      } catch (error: any) {
        result = { error: "ApiError", message: error.message };
      }
    } else {
      result = runPythonFallback(["compare", ...tickers]);
    }
    if (options.format === "json") { console.log(JSON.stringify(result, null, 2)); return; }
    if (result.error) { console.error(`ERROR: [${result.error}] | Cause: ${result.message}`); return; }
    console.log("\n=== STOCK COMPARISON SCREEN ===");
    console.log("--------------------------------------------------------------------------------");
    console.log(String("Ticker").padEnd(12) + String("Trend").padEnd(10) + String("Mom. Score").padEnd(12) + String("RS Score").padEnd(10) + String("P/E").padEnd(8) + String("Drawdown").padEnd(10) + "Flags");
    console.log("--------------------------------------------------------------------------------");
    result.forEach((stock: any) => {
      if (stock.error) {
        console.log(`${stock.ticker.padEnd(12)} [NOT FOUND: ${stock.message}]`);
        return;
      }
      const tc = stock.technical.trend === "bullish" ? "[32m▲[0m" : stock.technical.trend === "bearish" ? "[31m▼[0m" : "[33m━[0m";
      const pe = stock.valuation.pe_ratio !== null ? `${stock.valuation.pe_ratio}x` : "N/A";
      const flags = stock.risk.flags.length > 0 ? stock.risk.flags.join(", ") : "None";
      console.log(String(stock.ticker).padEnd(12) + tc.padEnd(16) + String(stock.momentum.momentum_score).padEnd(12) + String(stock.momentum.rs_score).padEnd(10) + pe.padEnd(8) + `-${stock.risk.drawdown_from_52w_high_pct}%`.padEnd(10) + flags);
    });
    console.log("--------------------------------------------------------------------------------");
    printDisclaimer("This platform provides educational and research information only. Consult a SEBI-registered advisor before trading.");
  });

// doctor
program.command("doctor")
  .description("Check system health: API connectivity, Node.js version, backend status")
  .action(async () => {
    console.log("\n=== NSE AI Agent - System Health Check ===");
    console.log("--------------------------------------------------------------------------------");
    const nv = process.version;
    const nodeOk = parseInt(nv.slice(1)) >= 18;
    console.log(`  Node.js:        ${nodeOk ? "[32m✓[0m " : "[31m✗[0m "} ${nv}${nodeOk ? "" : " (requires >= 18)"}`);
    console.log(`  API URL:        ${API_URL}`);
    const apiUp = await isApiRunning();
    if (apiUp) {
      console.log(`  Backend API:    [32m✓ Connected[0m (FastAPI on ${API_URL})`);
    } else {
      console.log(`  Backend API:    [33m⚠ Not[0m reachable - using local mock data fallback`);
    }
    const py = (() => {
      try { execSync("python --version", { stdio: "ignore" }); return true; } catch { return false; }
    })();
    console.log(`  Python fallback: ${py ? "[32m✓[0m  Available" : "[33m⚠[0m  Not found (optional)"}`);
    console.log("--------------------------------------------------------------------------------");
    if (apiUp) {
      console.log("  [32m✓ System[0m ready. All core features available.");
    } else {
      console.log("  [33m⚠ Running[0m in offline mode (mock data). Start the backend for live analysis.");
    }
    console.log("");
  });
// valuation
program.command("valuation <ticker>")
  .description("Run fundamental valuation analysis (Graham, DCF, PE-relative, PEG)")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (ticker, options) => {
    let result: any;
    const apiUp = await isApiRunning();
    if (apiUp) {
      try {
        const r = await axios.post(`${API_URL}/valuation`, { ticker });
        result = r.data;
      } catch (error: any) {
        result = error.response?.data || { error: "ApiError", message: error.message };
      }
    } else {
      result = runPythonFallback(["valuation", ticker]);
    }
    if (options.format === "json") { console.log(JSON.stringify(result, null, 2)); return; }
    if (result.error) { console.error(`ERROR: [${result.error}] | Cause: ${result.message}`); return; }
    console.log(`\n=== VALUATION: ${result.ticker} (${result.sector}) ===`);
    console.log("--------------------------------------------------------------------------------");
    console.log(`  CMP:              ₹${result.cmp?.toLocaleString()}`);
    console.log(`  P/E:              ${result.pe_ratio}x  (Industry: ${result.industry_pe}x)`);
    console.log(`  P/B:              ${result.pb_ratio}x`);
    console.log(`  EPS:              ₹${result.eps}`);
    console.log(`  ROE:              ${result.roe ? (result.roe * 100).toFixed(1) + "%" : "N/A"}`);
    console.log(`  D/E:              ${result.debt_to_equity}`);
    console.log("");
    console.log("  Valuation Models:");
    if (result.graham_number) {
      console.log(`  Graham Number:    ₹${result.graham_number.toLocaleString()} ${result.cmp < result.graham_number ? "(below)" : "(above)"}`);
    }
    if (result.pe_relative_value) {
      console.log(`  PE-Relative:      ₹${result.pe_relative_value.toLocaleString()} ${result.cmp < result.pe_relative_value ? "(below)" : "(above)"}`);
    }
    if (result.peg_ratio) {
      const pegLabel = result.peg_ratio < 1 ? "(undervalued)" : result.peg_ratio < 2 ? "(fair)" : "(overvalued)";
      console.log(`  PEG Ratio:        ${result.peg_ratio} ${pegLabel}`);
    }
    if (result.dcf_fair_value) {
      console.log(`  DCF Fair Value:   ₹${result.dcf_fair_value.toLocaleString()} ${result.cmp < result.dcf_fair_value ? "(below)" : "(above)"}`);
    }
    console.log("");
    const vc = result.verdict?.includes("UNDER") ? "[32mUNDERVALUED[0m" : result.verdict?.includes("OVER") ? "[31mOVERVALUED[0m" : "[33mFAIR[0m";
    console.log(`  Verdict:          ${vc} ${result.verdict}`);
    console.log(`  Avg Fair Value:   ₹${result.avg_fair_value?.toLocaleString()}`);
    console.log(`  Margin of Safety: ${result.margin_of_safety_pct}%`);
    printDisclaimer("For educational/research purposes only. Consult a SEBI-registered advisor before trading.");
  });
// risk
program.command("risk <ticker>")
  .description("Compute risk metrics: Beta, VaR, Sharpe, Sortino, Max Drawdown, Risk Score")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (ticker, options) => {
    let result: any;
    const apiUp = await isApiRunning();
    if (apiUp) {
      try {
        const r = await axios.post(`${API_URL}/risk`, { ticker });
        result = r.data;
      } catch (error: any) {
        result = error.response?.data || { error: "ApiError", message: error.message };
      }
    } else {
      result = runPythonFallback(["risk", ticker]);
    }
    if (options.format === "json") { console.log(JSON.stringify(result, null, 2)); return; }
    if (result.error) { console.error(`ERROR: [${result.error}] | Cause: ${result.message}`); return; }
    const sc = (result.risk_score || 0) <= 40 ? "[32mLOW[0m" : (result.risk_score || 0) <= 70 ? "[33mMED[0m" : "[31mHIGH[0m";
    console.log(`\n=== RISK ANALYSIS: ${result.ticker} ===`);
    console.log("--------------------------------------------------------------------------------");
    console.log(`  Total Return:    ${result.total_return >= 0 ? "+" : ""}${result.total_return}%`);
    console.log(`  Annual Return:   ${result.annual_return >= 0 ? "+" : ""}${result.annual_return}%`);
    console.log(`  Volatility:      ${result.volatility}%`);
    console.log(`  Beta:            ${result.beta}`);
    console.log(`  VaR (95%):       ${result.var_95_daily}%/day`);
    console.log(`  VaR (99%):       ${result.var_99_daily}%/day`);
    console.log(`  Max Drawdown:    ${result.max_drawdown}%`);
    console.log(`  Sharpe Ratio:    ${result.sharpe_ratio}`);
    console.log(`  Sortino Ratio:   ${result.sortino_ratio}`);
    console.log("");
    console.log(`  Risk Score:      ${sc} ${result.risk_score}/100 - ${result.rating}`);
    printDisclaimer("Risk metrics are based on historical data and do not predict future risk. For educational/research purposes only.");
  });
// backtest
program.command("backtest <ticker>")
  .description("Backtest a trading strategy on historical data")
  .requiredOption("--strategy <strategy>", "Strategy: triple-ema-crossover, rsi-mean-reversion, breakout-retest, ema-pullback")
  .option("--capital <capital>", "Starting capital in INR", "1000000")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (ticker, options) => {
    let result: any;
    const apiUp = await isApiRunning();
    if (apiUp) {
      try {
        const r = await axios.post(`${API_URL}/backtest`, {
          ticker,
          strategy: options.strategy,
          capital: parseFloat(options.capital),
        });
        result = r.data;
      } catch (error: any) {
        result = error.response?.data || { error: "ApiError", message: error.message };
      }
    } else {
      result = runPythonFallback(["backtest", ticker, "--strategy", options.strategy, "--capital", options.capital]);
    }
    if (options.format === "json") { console.log(JSON.stringify(result, null, 2)); return; }
    if (result.error) { console.error(`ERROR: [${result.error}] | Cause: ${result.message}`); return; }
    console.log(`\n=== BACKTEST: ${result.ticker} (${result.strategy}) ===`);
    console.log(`  Period:            ${result.period_start} -> ${result.period_end}`);
    console.log("--------------------------------------------------------------------------------");
    console.log(`  Starting Capital:  ₹${result.starting_capital?.toLocaleString()}`);
    console.log(`  Ending Capital:    ₹${result.ending_capital?.toLocaleString()}`);
    const rc = (result.total_return || 0) >= 0 ? "+" : "";
    console.log(`  Total Return:      ${rc}${result.total_return}%`);
    console.log(`  CAGR:              ${result.cagr >= 0 ? "+" : ""}${result.cagr}%`);
    console.log(`  Max Drawdown:      ${result.max_drawdown}%`);
    console.log(`  Win Rate:          ${result.win_rate}%`);
    console.log(`  Profit Factor:     ${result.profit_factor}`);
    console.log(`  Total Trades:      ${result.total_trades}`);
    console.log(`  Avg Holding:       ${result.avg_holding_days} days`);
    console.log(`  Risk:Reward:       ${result.risk_reward}`);
    if (result.trades && result.trades.length > 0) {
      console.log("");
      console.log("  Recent Trades:");
      result.trades.slice(-5).forEach((t: any) => {
        const tag = t.pnl >= 0 ? "[32m✔ WIN [0m" : "[31m✘ LOSS[0m";
        console.log(`    ${tag} ${t.entry_date} -> ${t.exit_date} | ₹${t.entry_price.toLocaleString()} -> ₹${t.exit_price.toLocaleString()} | ${t.pnl >= 0 ? "+" : ""}₹${t.pnl.toLocaleString()} (${t.return_pct >= 0 ? "+" : ""}${t.return_pct}%)`);
      });
    }
    printDisclaimer("Past backtest results do not guarantee future performance. For educational/research purposes only.");
  });
// mcp
const mcpCmd = program.command("mcp").description("Manage the NSE AI Agent MCP server");

mcpCmd.command("serve")
  .description("Start the MCP server over stdio transport (for agent integrations)")
  .action(() => {
    try {
      execSync(`python "${mcpServerPath}"`, { stdio: "inherit" });
    } catch (error: any) {
      console.error(`Failed to start MCP server: ${error.message}`);
      console.error("Make sure Python and required packages are installed:");
      console.error("  pip install -r packages/core/requirements.txt");
      process.exit(1);
    }
  });

mcpCmd.command("config")
  .description("Print MCP configuration snippets for Claude Desktop, Cursor, and OpenCode")
  .option("--target <target>", "Config target: claude, cursor, opencode, all", "all")
  .action((options) => {
    const sp = mcpServerPath.replace(/\\/g, "/");
    const claude = { mcpServers: { "nse-ai-agent": { command: "python", args: [sp] } } };
    const cursor = { mcpServers: { "nse-ai-agent": { command: "python", args: [sp] } } };
    const opencode = { mcp: { servers: { "nse-ai-agent": { type: "stdio", command: "python", args: [sp] } } } };
    const t = options.target.toLowerCase();
    if (t === "claude" || t === "all") {
      console.log("\n=== Claude Desktop Config (claude_desktop_config.json) ===\n");
      console.log(JSON.stringify(claude, null, 2));
    }
    if (t === "cursor" || t === "all") {
      console.log("\n=== Cursor Config (.cursor/mcp.json) ===\n");
      console.log(JSON.stringify(cursor, null, 2));
    }
    if (t === "opencode" || t === "all") {
      console.log("\n=== OpenCode Config (opencode.json) ===\n");
      console.log(JSON.stringify(opencode, null, 2));
    }
    console.log("\nTip: Run 'nse-agent mcp serve' to start the MCP server manually.\n");
  });

program.parse(process.argv);
