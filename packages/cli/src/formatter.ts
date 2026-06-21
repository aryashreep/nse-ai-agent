// Formatter module - extracted formatting functions for testable unit tests

const SEP = '--------------------------------------------------------------------------------';
const G = '\x1b[32m';
const R = '\x1b[31m';
const Y = '\x1b[33m';
const D = '\x1b[0m';

export function printDisclaimer(d: string): string[] {
  return ['', SEP, 'DISCLAIMER: ' + d, SEP, ''];
}

export function trendLabel(trend: string): string {
  if (trend === 'bullish') return G + '\u25B2' + D;
  if (trend === 'bearish') return R + '\u25BC' + D;
  return Y + '\u2501' + D;
}

export function trendText(trend: string): string {
  return trendLabel(trend) + ' ' + trend.toUpperCase();
}

export function riskScoreLabel(score: number): string {
  if (score <= 40) return G + 'LOW' + D;
  if (score <= 70) return Y + 'MED' + D;
  return R + 'HIGH' + D;
}

export function verdictLabel(verdict: string): string {
  if (verdict && verdict.indexOf('UNDER') >= 0) return G + 'UNDERVALUED' + D;
  if (verdict && verdict.indexOf('OVER') >= 0) return R + 'OVERVALUED' + D;
  return Y + 'FAIR' + D;
}

export function tradeLabel(pnl: number): string {
  return pnl >= 0 ? G + '\u2713 WIN ' + D : R + '\u2717 LOSS' + D;
}

export function rupee(val: number | null | undefined): string {
  if (val === null || val === undefined) return 'N/A';
  return '\u20B9' + val.toLocaleString();
}

export function formatAnalyze(result: any): string[] {
  const lines: string[] = [];
  lines.push('\n=== NSE AGENTIC RESEARCH: ' + result.ticker + ' (' + result.as_of + ') ===');
  lines.push('Source Provider: ' + result.source.toUpperCase());
  lines.push(SEP);
  lines.push('Technical Snapshot:');
  lines.push('  Trend:           ' + trendText(result.technical.trend));
  lines.push('  EMA 21 / 55:     ' + rupee(result.technical.ema_21) + ' / ' + rupee(result.technical.ema_55));
  lines.push('  EMA 200:         ' + rupee(result.technical.ema_200));
  var pct = result.technical.price_vs_ema200_pct;
  lines.push('  vs EMA 200:      ' + (pct > 0 ? '+' : '') + pct + '%');
  lines.push('');
  lines.push('Momentum Profile:');
  lines.push('  Composite Score: ' + result.momentum.momentum_score + '/100');
  lines.push('  RS Score:        ' + result.momentum.rs_score + '/100');
  lines.push('  RS Velocity:     ' + (result.momentum.rs_velocity > 0 ? '+' : '') + result.momentum.rs_velocity);
  lines.push('  Volume Surge:    ' + (result.momentum.volume_expansion ? 'YES' : 'NO'));
  lines.push('  ATR Expansion:   ' + (result.momentum.atr_expansion ? 'YES' : 'NO'));
  lines.push('');
  lines.push('Valuation Multiples:');
  lines.push('  P/E Ratio:       ' + (result.valuation.pe_ratio !== null ? result.valuation.pe_ratio + 'x' : 'N/A'));
  lines.push('  P/B Ratio:       ' + (result.valuation.pb_ratio !== null ? result.valuation.pb_ratio + 'x' : 'N/A'));
  lines.push('  Dividend Yield:  ' + (result.valuation.dividend_yield !== null ? result.valuation.dividend_yield + '%' : 'N/A'));
  lines.push('');
  lines.push('Risk Assessment:');
  lines.push('  Daily Vol (ATR): ' + result.risk.atr_pct + '%');
  lines.push('  Drawdown (52w):  -' + result.risk.drawdown_from_52w_high_pct + '%');
  if (result.risk.flags && result.risk.flags.length > 0) {
    lines.push('  Risk Flags:      ' + result.risk.flags.join(', '));
  } else {
    lines.push('  Risk Flags:      NONE');
  }
  lines.push.apply(lines, printDisclaimer(result.disclaimer));
  return lines;
}

export function formatValuation(result: any): string[] {
  const lines: string[] = [];
  lines.push('\n=== VALUATION: ' + result.ticker + ' (' + result.sector + ') ===');
  lines.push(SEP);
  lines.push('  CMP:              ' + rupee(result.cmp));
  lines.push('  P/E:              ' + result.pe_ratio + 'x  (Industry: ' + result.industry_pe + 'x)');
  lines.push('  P/B:              ' + result.pb_ratio + 'x');
  lines.push('  EPS:              ' + rupee(result.eps));
  lines.push('  ROE:              ' + (result.roe ? (result.roe * 100).toFixed(1) + '%' : 'N/A'));
  lines.push('  D/E:              ' + result.debt_to_equity);
  lines.push('');
  lines.push('  Valuation Models:');
  if (result.graham_number) {
    var below = result.cmp < result.graham_number ? '(below)' : '(above)';
    lines.push('  Graham Number:    ' + rupee(result.graham_number) + ' ' + below);
  }
  if (result.pe_relative_value) {
    below = result.cmp < result.pe_relative_value ? '(below)' : '(above)';
    lines.push('  PE-Relative:      ' + rupee(result.pe_relative_value) + ' ' + below);
  }
  if (result.peg_ratio) {
    var pegLabel = result.peg_ratio < 1 ? '(undervalued)' : result.peg_ratio < 2 ? '(fair)' : '(overvalued)';
    lines.push('  PEG Ratio:        ' + result.peg_ratio + ' ' + pegLabel);
  }
  if (result.dcf_fair_value) {
    below = result.cmp < result.dcf_fair_value ? '(below)' : '(above)';
    lines.push('  DCF Fair Value:   ' + rupee(result.dcf_fair_value) + ' ' + below);
  }
  lines.push('');
  lines.push('  Verdict:          ' + verdictLabel(result.verdict) + ' ' + result.verdict);
  lines.push('  Avg Fair Value:   ' + rupee(result.avg_fair_value));
  lines.push('  Margin of Safety: ' + result.margin_of_safety_pct + '%');
  lines.push.apply(lines, printDisclaimer('For educational/research purposes only. Consult a SEBI-registered advisor before trading.'));
  return lines;
}

export function formatRisk(result: any): string[] {
  const lines: string[] = [];
  var sc = riskScoreLabel(result.risk_score || 0);
  lines.push('\n=== RISK ANALYSIS: ' + result.ticker + ' ===');
  lines.push(SEP);
  lines.push('  Total Return:    ' + (result.total_return >= 0 ? '+' : '') + result.total_return + '%');
  lines.push('  Annual Return:   ' + (result.annual_return >= 0 ? '+' : '') + result.annual_return + '%');
  lines.push('  Volatility:      ' + result.volatility + '%');
  lines.push('  Beta:            ' + result.beta);
  lines.push('  VaR (95%):       ' + result.var_95_daily + '%/day');
  lines.push('  VaR (99%):       ' + result.var_99_daily + '%/day');
  lines.push('  Max Drawdown:    ' + result.max_drawdown + '%');
  lines.push('  Sharpe Ratio:    ' + result.sharpe_ratio);
  lines.push('  Sortino Ratio:   ' + result.sortino_ratio);
  lines.push('');
  lines.push('  Risk Score:      ' + sc + ' ' + result.risk_score + '/100 - ' + result.rating);
  lines.push.apply(lines, printDisclaimer('Risk metrics are based on historical data and do not predict future risk. For educational/research purposes only.'));
  return lines;
}

export function formatBacktest(result: any): string[] {
  const lines: string[] = [];
  var rc = (result.total_return || 0) >= 0 ? '+' : '';
  lines.push('\n=== BACKTEST: ' + result.ticker + ' (' + result.strategy + ') ===');
  lines.push('  Period:            ' + result.period_start + ' -> ' + result.period_end);
  lines.push(SEP);
  lines.push('  Starting Capital:  ' + rupee(result.starting_capital));
  lines.push('  Ending Capital:    ' + rupee(result.ending_capital));
  lines.push('  Total Return:      ' + rc + result.total_return + '%');
  lines.push('  CAGR:              ' + (result.cagr >= 0 ? '+' : '') + result.cagr + '%');
  lines.push('  Max Drawdown:      ' + result.max_drawdown + '%');
  lines.push('  Win Rate:          ' + result.win_rate + '%');
  lines.push('  Profit Factor:     ' + result.profit_factor);
  lines.push('  Total Trades:      ' + result.total_trades);
  lines.push('  Avg Holding:       ' + result.avg_holding_days + ' days');
  lines.push('  Risk:Reward:       ' + result.risk_reward);
  if (result.trades && result.trades.length > 0) {
    lines.push('');
    lines.push('  Recent Trades:');
    result.trades.slice(-5).forEach(function(t: any) {
      var tag = tradeLabel(t.pnl);
      var sign = t.pnl >= 0 ? '+' : '';
      var pctSign = t.return_pct >= 0 ? '+' : '';
      lines.push('    ' + tag + ' ' + t.entry_date + ' -> ' + t.exit_date + ' | ' + rupee(t.entry_price) + ' -> ' + rupee(t.exit_price) + ' | ' + sign + rupee(t.pnl) + ' (' + pctSign + t.return_pct + '%)');
    });
  }
  lines.push.apply(lines, printDisclaimer('Past backtest results do not guarantee future performance. For educational/research purposes only.'));
  return lines;
}

export function formatScreenHeader(sector?: string): string[] {
  const lines: string[] = [];
  lines.push('\n=== MOMENTUM SCREENER RESULTS (Universe: 20 Tickers) ===');
  if (sector) lines.push('Sector Filter: ' + sector);
  lines.push(SEP);
  lines.push(
    'Rank'.padEnd(5) +
    'Ticker'.padEnd(12) +
    'Sector'.padEnd(20) +
    'Trend'.padEnd(10) +
    'Mom. Score'.padEnd(12) +
    'Risk Flags'
  );
  lines.push(SEP);
  return lines;
}

export function formatScreenRow(index: number, stock: any): string {
  var tc = trendLabel(stock.trend);
  var flags = stock.risk_flags.length > 0 ? stock.risk_flags.join(', ') : 'None';
  return (
    String(index + 1).padEnd(5) +
    String(stock.ticker).padEnd(12) +
    String(stock.sector).padEnd(20) +
    tc.padEnd(21) +
    String(stock.momentum_score).padEnd(12) +
    flags
  );
}

export function formatCompareHeader(): string[] {
  const lines: string[] = [];
  lines.push('\n=== STOCK COMPARISON SCREEN ===');
  lines.push(SEP);
  lines.push(
    'Ticker'.padEnd(12) +
    'Trend'.padEnd(10) +
    'Mom. Score'.padEnd(12) +
    'RS Score'.padEnd(10) +
    'P/E'.padEnd(8) +
    'Drawdown'.padEnd(10) +
    'Flags'
  );
  lines.push(SEP);
  return lines;
}

export function formatCompareRow(stock: any): string {
  var tc = trendLabel(stock.technical.trend);
  var pe = stock.valuation.pe_ratio !== null ? stock.valuation.pe_ratio + 'x' : 'N/A';
  var flags = stock.risk.flags.length > 0 ? stock.risk.flags.join(', ') : 'None';
  return (
    String(stock.ticker).padEnd(12) +
    tc.padEnd(21) +
    String(stock.momentum.momentum_score).padEnd(12) +
    String(stock.momentum.rs_score).padEnd(10) +
    pe.padEnd(8) +
    ('-' + stock.risk.drawdown_from_52w_high_pct + '%').padEnd(10) +
    flags
  );
}
