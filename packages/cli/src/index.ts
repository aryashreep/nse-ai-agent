import { Command } from "commander";
import axios from "axios";
import { execSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

const API_URL = "http://127.0.0.1:8000";
const program = new Command();

// Resolve paths to the local python analyzer
const pythonAnalyzerPath = path.resolve(__dirname, "../../core/src/local_analyzer.py");

/**
 * Checks if the FastAPI server is running
 */
async function isApiRunning(): Promise<boolean> {
  try {
    const response = await axios.get(`${API_URL}/health`, { timeout: 800 });
    return response.status === 200 && response.data.status === "healthy";
  } catch (e) {
    return false;
  }
}

/**
 * Executes the python script locally as a fallback
 */
function runPythonFallback(args: string[]): any {
  // Format execution arguments
  const pythonCmd = `python "${pythonAnalyzerPath}" ${args.join(" ")}`;
  try {
    const stdout = execSync(pythonCmd, { encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
    return JSON.parse(stdout.trim());
  } catch (error: any) {
    const errorMsg = error.stderr || error.message || "";
    return {
      error: "LocalExecutionError",
      message: `Failed to run local python analyzer: ${errorMsg}`
    };
  }
}

/**
 * Print SEBI Disclaimer
 */
function printDisclaimer(disclaimer: string) {
  console.log("\n--------------------------------------------------------------------------------");
  console.log(`⚠️ DISCLAIMER: ${disclaimer}`);
  console.log("--------------------------------------------------------------------------------\n");
}

// Set up commander program
program
  .name("nse-agent")
  .description("NSE Agentic Research Platform CLI client")
  .version("1.0.0");

// Command: analyze
program
  .command("analyze <ticker>")
  .description("Perform full analysis on an NSE stock ticker")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (ticker, options) => {
    let result: any;
    const apiUp = await isApiRunning();

    if (apiUp) {
      try {
        const response = await axios.post(`${API_URL}/analyze`, { ticker });
        result = response.data;
      } catch (error: any) {
        if (error.response && error.response.status === 404) {
          result = { error: "NotFoundError", message: `Ticker ${ticker} not found.` };
        } else {
          result = { error: "ApiError", message: error.message };
        }
      }
    } else {
      // Fallback
      result = runPythonFallback(["analyze", ticker]);
    }

    // Output formatting
    if (options.format === "json") {
      console.log(JSON.stringify(result, null, 2));
      return;
    }

    if (result.error) {
      console.error(`\x1b[31m⚠️ ERROR: [${result.error}] | Cause: ${result.message}\x1b[0m`);
      return;
    }

    // Default Human Readable Print
    console.log(`\n\x1b[1m=== NSE AGENTIC RESEARCH: ${result.ticker} (${result.as_of}) ===\x1b[0m`);
    console.log(`Source Provider: ${result.source.toUpperCase()}`);
    console.log("--------------------------------------------------------------------------------");
    
    // Technicals
    const trendColor = result.technical.trend === "bullish" ? "\x1b[32m" : result.technical.trend === "bearish" ? "\x1b[31m" : "\x1b[33m";
    console.log(`\x1b[1mTechnical Snapshot:\x1b[0m`);
    console.log(`  Trend:           ${trendColor}${result.technical.trend.toUpperCase()}\x1b[0m`);
    console.log(`  EMA 21 / 55:     ₹${result.technical.ema_21} / ₹${result.technical.ema_55}`);
    console.log(`  EMA 200:         ₹${result.technical.ema_200}`);
    console.log(`  vs EMA 200:      ${result.technical.price_vs_ema200_pct > 0 ? "+" : ""}${result.technical.price_vs_ema200_pct}%`);
    
    // Momentum
    console.log(`\n\x1b[1mMomentum Profile:\x1b[0m`);
    console.log(`  Composite Score: \x1b[35m${result.momentum.momentum_score}/100\x1b[0m`);
    console.log(`  RS Score:        ${result.momentum.rs_score}/100`);
    console.log(`  RS Velocity:     ${result.momentum.rs_velocity > 0 ? "+" : ""}${result.momentum.rs_velocity}`);
    console.log(`  Volume Surge:    ${result.momentum.volume_expansion ? "🟢 YES" : "⚪ NO"}`);
    console.log(`  ATR Expansion:   ${result.momentum.atr_expansion ? "🟡 YES" : "⚪ NO"}`);
    
    // Valuation
    console.log(`\n\x1b[1mValuation Multiples:\x1b[0m`);
    console.log(`  P/E Ratio:       ${result.valuation.pe_ratio !== null ? result.valuation.pe_ratio + "x" : "N/A"}`);
    console.log(`  P/B Ratio:       ${result.valuation.pb_ratio !== null ? result.valuation.pb_ratio + "x" : "N/A"}`);
    console.log(`  Dividend Yield:  ${result.valuation.dividend_yield !== null ? result.valuation.dividend_yield + "%" : "N/A"}`);
    
    // Risk
    console.log(`\n\x1b[1mRisk Assessment:\x1b[0m`);
    console.log(`  Daily Vol (ATR): ${result.risk.atr_pct}%`);
    console.log(`  Drawdown (52w):  -${result.risk.drawdown_from_52w_high_pct}%`);
    
    const riskFlags = result.risk.flags;
    if (riskFlags && riskFlags.length > 0) {
      console.log(`  Risk Flags:      \x1b[31m🚨 ${riskFlags.join(", ")}\x1b[0m`);
    } else {
      console.log(`  Risk Flags:      🟢 NONE`);
    }

    printDisclaimer(result.disclaimer);
  });

// Command: screen
program
  .command("screen [strategy]")
  .description("Screen stocks for momentum setups")
  .option("--sector <sector>", "Filter results by sector")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (strategy = "momentum", options) => {
    let result: any;
    const apiUp = await isApiRunning();

    if (apiUp) {
      try {
        const response = await axios.post(`${API_URL}/screen`, {
          strategy,
          sector: options.sector
        });
        result = response.data;
      } catch (error: any) {
        result = { error: "ApiError", message: error.message };
      }
    } else {
      // Fallback
      const pyArgs = ["screen", strategy];
      if (options.sector) {
        pyArgs.push("--sector", `"${options.sector}"`);
      }
      result = runPythonFallback(pyArgs);
    }

    if (options.format === "json") {
      console.log(JSON.stringify(result, null, 2));
      return;
    }

    if (result.error) {
      console.error(`\x1b[31m⚠️ ERROR: [${result.error}] | Cause: ${result.message}\x1b[0m`);
      return;
    }

    // Default Human Readable Table print
    console.log(`\n\x1b[1m=== MOMENTUM SCREENER RESULTS (Universe: 20 Tickers) ===\x1b[0m`);
    if (options.sector) console.log(`Sector Filter: ${options.sector}`);
    console.log("--------------------------------------------------------------------------------");
    console.log(
      String("Rank").padEnd(5) + 
      String("Ticker").padEnd(12) + 
      String("Sector").padEnd(20) + 
      String("Trend").padEnd(10) + 
      String("Mom. Score").padEnd(12) + 
      String("Risk Flags")
    );
    console.log("--------------------------------------------------------------------------------");
    
    result.forEach((stock: any, index: number) => {
      const trendColor = stock.trend === "bullish" ? "\x1b[32m" : stock.trend === "bearish" ? "\x1b[31m" : "\x1b[33m";
      const trendStr = `${trendColor}${stock.trend.toUpperCase()}\x1b[0m`;
      const flagStr = stock.risk_flags.length > 0 ? `🚨 ${stock.risk_flags.join(", ")}` : "None";
      
      console.log(
        String(index + 1).padEnd(5) + 
        String(stock.ticker).padEnd(12) + 
        String(stock.sector).padEnd(20) + 
        trendStr.padEnd(19) + // pad adjustment for ANSI escape codes length
        String(stock.momentum_score).padEnd(12) + 
        flagStr
      );
    });
    console.log("--------------------------------------------------------------------------------");
    printDisclaimer("This platform provides educational and research information only. Consult a SEBI-registered advisor before trading.");
  });

// Command: compare
program
  .command("compare <tickers...>")
  .description("Compare multiple NSE stock tickers side-by-side")
  .option("-f, --format <format>", "Output format: text, json", "text")
  .action(async (tickers, options) => {
    let result: any;
    const apiUp = await isApiRunning();

    if (apiUp) {
      try {
        const response = await axios.post(`${API_URL}/compare`, { tickers });
        result = response.data;
      } catch (error: any) {
        result = { error: "ApiError", message: error.message };
      }
    } else {
      // Fallback
      result = runPythonFallback(["compare", ...tickers]);
    }

    if (options.format === "json") {
      console.log(JSON.stringify(result, null, 2));
      return;
    }

    if (result.error) {
      console.error(`\x1b[31m⚠️ ERROR: [${result.error}] | Cause: ${result.message}\x1b[0m`);
      return;
    }

    // Default Human Readable print
    console.log(`\n\x1b[1m=== STOCK COMPARISON SCREEN ===\x1b[0m`);
    console.log("--------------------------------------------------------------------------------");
    console.log(
      String("Ticker").padEnd(12) + 
      String("Trend").padEnd(10) + 
      String("Mom. Score").padEnd(12) + 
      String("RS Score").padEnd(10) + 
      String("P/E").padEnd(8) + 
      String("Drawdown").padEnd(10) + 
      String("Flags")
    );
    console.log("--------------------------------------------------------------------------------");

    result.forEach((stock: any) => {
      if (stock.error) {
        console.log(`${stock.ticker.padEnd(12)} \x1b[31m[NOT FOUND: ${stock.message}]\x1b[0m`);
        return;
      }
      
      const trendColor = stock.technical.trend === "bullish" ? "\x1b[32m" : stock.technical.trend === "bearish" ? "\x1b[31m" : "\x1b[33m";
      const peStr = stock.valuation.pe_ratio !== null ? `${stock.valuation.pe_ratio}x` : "N/A";
      const flags = stock.risk.flags.length > 0 ? `🚨 ${stock.risk.flags.join(", ")}` : "None";
      
      console.log(
        String(stock.ticker).padEnd(12) + 
        `${trendColor}${stock.technical.trend.toUpperCase()}\x1b[0m`.padEnd(19) + 
        String(stock.momentum.momentum_score).padEnd(12) + 
        String(stock.momentum.rs_score).padEnd(10) + 
        peStr.padEnd(8) + 
        `-${stock.risk.drawdown_from_52w_high_pct}%`.padEnd(10) + 
        flags
      );
    });
    console.log("--------------------------------------------------------------------------------");
    printDisclaimer("This platform provides educational and research information only. Consult a SEBI-registered advisor before trading.");
  });

program.parse(process.argv);
