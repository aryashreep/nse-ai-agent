import {
  printDisclaimer,
  trendLabel,
  trendText,
  riskScoreLabel,
  verdictLabel,
  tradeLabel,
  rupee,
  formatAnalyze,
  formatValuation,
  formatRisk,
  formatBacktest,
  formatScreenHeader,
  formatScreenRow,
  formatCompareHeader,
  formatCompareRow,
} from './formatter';

// ─── Mock data factories ──────────────────────────────────────
const mockAnalyzeResult: any = {
  ticker: 'ITC', as_of: '2024-01-15', source: 'mock',
  technical: { trend: 'bullish', ema_21: 450.5, ema_55: 435.2, ema_200: 420.0, price_vs_ema200_pct: 5.5 },
  momentum: { momentum_score: 72, rs_score: 68, rs_velocity: 2.3, volume_expansion: true, atr_expansion: false },
  valuation: { pe_ratio: 28.5, pb_ratio: 5.2, dividend_yield: 1.2 },
  risk: { atr_pct: 1.8, drawdown_from_52w_high_pct: 8.5, flags: ['High PE'] },
  disclaimer: 'Educational purposes only.',
};

const mockValuationResult: any = {
  ticker: 'ITC', sector: 'FMCG', cmp: 450.0, pe_ratio: 28.5, industry_pe: 35.0,
  pb_ratio: 5.2, eps: 15.8, roe: 0.28, debt_to_equity: 0.05,
  graham_number: 320.0, pe_relative_value: 480.0, peg_ratio: 1.2, dcf_fair_value: 520.0,
  verdict: 'UNDERVALUED - Trading below Graham Number',
  avg_fair_value: 455.0, margin_of_safety_pct: 1.1,
};

const mockRiskResult: any = {
  ticker: 'ITC', total_return: 15.5, annual_return: 12.3, volatility: 18.5,
  beta: 0.85, var_95_daily: 2.1, var_99_daily: 3.2, max_drawdown: 15.0,
  sharpe_ratio: 1.2, sortino_ratio: 1.8, risk_score: 45, rating: 'Moderate',
};

const mockBacktestResult: any = {
  ticker: 'ITC', strategy: 'triple-ema-crossover',
  period_start: '2023-01-01', period_end: '2024-01-01',
  starting_capital: 1000000, ending_capital: 1150000,
  total_return: 15.0, cagr: 15.0, max_drawdown: 8.5,
  win_rate: 65.0, profit_factor: 2.1, total_trades: 24,
  avg_holding_days: 12, risk_reward: '1:2.5',
  trades: [
    { entry_date: '2023-01-15', exit_date: '2023-02-01', entry_price: 420.0, exit_price: 450.0, pnl: 30000, return_pct: 7.14 },
    { entry_date: '2023-03-10', exit_date: '2023-03-25', entry_price: 445.0, exit_price: 430.0, pnl: -15000, return_pct: -3.37 },
  ],
};

const mockScreenStocks: any[] = [
  { ticker: 'ITC', sector: 'FMCG', trend: 'bullish', momentum_score: 72, risk_flags: [] },
  { ticker: 'RELIANCE', sector: 'Energy', trend: 'bearish', momentum_score: 35, risk_flags: ['High PE'] },
];

const mockCompareStocks: any[] = [
  {
    ticker: 'ITC', technical: { trend: 'bullish' },
    momentum: { momentum_score: 72 }, valuation: { pe_ratio: 28.5 },
    risk: { drawdown_from_52w_high_pct: 8.5, flags: [] },
  },
  {
    ticker: 'RELIANCE', technical: { trend: 'bearish' },
    momentum: { momentum_score: 35 }, valuation: { pe_ratio: null },
    risk: { drawdown_from_52w_high_pct: 15.2, flags: ['High Debt'] },
  },
];

// ─── Tests ───────────────────────────────────────────────────

describe('printDisclaimer', () => {
  it('should return array with disclaimer text and separators', () => {
    const lines = printDisclaimer('Test disclaimer.');
    expect(lines).toHaveLength(5);
    expect(lines[1]).toContain('---');
    expect(lines[2]).toBe('DISCLAIMER: Test disclaimer.');
    expect(lines[3]).toContain('---');
  });
});

describe('trendLabel', () => {
  it('should return green for bullish', () => {
    const label = trendLabel('bullish');
    expect(label).toContain('\x1b[32m');
    expect(label).toContain('\u25B2');
  });

  it('should return red for bearish', () => {
    const label = trendLabel('bearish');
    expect(label).toContain('\x1b[31m');
    expect(label).toContain('\u25BC');
  });

  it('should return yellow for neutral', () => {
    const label = trendLabel('neutral');
    expect(label).toContain('\x1b[33m');
    expect(label).toContain('\u2501');
  });
});

describe('trendText', () => {
  it('should combine label with uppercased trend', () => {
    const text = trendText('bullish');
    expect(text).toContain('BULLISH');
    expect(text).toContain('\u25B2');
  });
});

describe('riskScoreLabel', () => {
  it('should return green LOW for score <= 40', () => {
    const label = riskScoreLabel(25);
    expect(label).toContain('LOW');
    expect(label).toContain('\x1b[32m');
  });

  it('should return yellow MED for score 41-70', () => {
    const label = riskScoreLabel(55);
    expect(label).toContain('MED');
    expect(label).toContain('\x1b[33m');
  });

  it('should return red HIGH for score > 70', () => {
    const label = riskScoreLabel(85);
    expect(label).toContain('HIGH');
    expect(label).toContain('\x1b[31m');
  });

  it('should handle boundary: 40 is LOW', () => {
    expect(riskScoreLabel(40)).toContain('LOW');
  });

  it('should handle boundary: 41 is MED', () => {
    expect(riskScoreLabel(41)).toContain('MED');
  });

  it('should handle boundary: 70 is MED', () => {
    expect(riskScoreLabel(70)).toContain('MED');
  });

  it('should handle boundary: 71 is HIGH', () => {
    expect(riskScoreLabel(71)).toContain('HIGH');
  });
});

describe('verdictLabel', () => {
  it('should return green for UNDERVALUED', () => {
    const label = verdictLabel('UNDERVALUED - Good');
    expect(label).toContain('UNDERVALUED');
    expect(label).toContain('\x1b[32m');
  });

  it('should return red for OVERVALUED', () => {
    const label = verdictLabel('OVERVALUED - Bad');
    expect(label).toContain('OVERVALUED');
    expect(label).toContain('\x1b[31m');
  });

  it('should return yellow for FAIR', () => {
    const label = verdictLabel('FAIR');
    expect(label).toContain('FAIR');
    expect(label).toContain('\x1b[33m');
  });

  it('should handle null/undefined gracefully', () => {
    expect(verdictLabel(null as any)).toContain('FAIR');
    expect(verdictLabel(undefined as any)).toContain('FAIR');
  });
});

describe('tradeLabel', () => {
  it('should return green checkmark for positive PnL', () => {
    const label = tradeLabel(30000);
    expect(label).toContain('WIN');
    expect(label).toContain('\x1b[32m');
    expect(label).toContain('\u2713');
  });

  it('should return red cross for negative PnL', () => {
    const label = tradeLabel(-15000);
    expect(label).toContain('LOSS');
    expect(label).toContain('\x1b[31m');
    expect(label).toContain('\u2717');
  });

  it('should treat zero PnL as win', () => {
    const label = tradeLabel(0);
    expect(label).toContain('WIN');
  });
});

describe('rupee', () => {
  it('should format number with rupee symbol', () => {
    var result = rupee(450);
    expect(result).toContain('\u20B9');
    expect(result).toContain('450');
  });

  it('should return N/A for null', () => {
    expect(rupee(null)).toBe('N/A');
  });

  it('should return N/A for undefined', () => {
    expect(rupee(undefined)).toBe('N/A');
  });

  it('should use toLocaleString for large numbers', () => {
    var result = rupee(1000000);
    expect(result).toContain('\u20B9');
    expect(result).toContain('1');
  });
});

describe('formatAnalyze', () => {
  it('should include ticker and date in header', () => {
    var lines = formatAnalyze(mockAnalyzeResult);
    var text = lines.join('\n');
    expect(text).toContain('ITC');
    expect(text).toContain('2024-01-15');
    expect(text).toContain('NSE AGENTIC RESEARCH');
  });

  it('should include all section headers', () => {
    var lines = formatAnalyze(mockAnalyzeResult);
    var text = lines.join('\n');
    expect(text).toContain('Technical Snapshot:');
    expect(text).toContain('Momentum Profile:');
    expect(text).toContain('Valuation Multiples:');
    expect(text).toContain('Risk Assessment:');
  });

  it('should show bullish trend indicator', () => {
    var lines = formatAnalyze(mockAnalyzeResult);
    var text = lines.join('\n');
    expect(text).toContain('BULLISH');
    expect(text).toContain('\u25B2');
  });

  it('should show bearish trend indicator for bearish data', () => {
    var bearishResult = { ...mockAnalyzeResult, technical: { ...mockAnalyzeResult.technical, trend: 'bearish' } };
    var lines = formatAnalyze(bearishResult);
    var text = lines.join('\n');
    expect(text).toContain('BEARISH');
    expect(text).toContain('\u25BC');
  });

  it('should include disclaimer', () => {
    var lines = formatAnalyze(mockAnalyzeResult);
    var text = lines.join('\n');
    expect(text).toContain('DISCLAIMER:');
    expect(text).toContain('Educational purposes only.');
  });

  it('should display risk flags', () => {
    var lines = formatAnalyze(mockAnalyzeResult);
    var text = lines.join('\n');
    expect(text).toContain('High PE');
  });

  it('should show NONE for empty risk flags', () => {
    var noFlags = { ...mockAnalyzeResult, risk: { ...mockAnalyzeResult.risk, flags: [] } };
    var lines = formatAnalyze(noFlags);
    var text = lines.join('\n');
    expect(text).toContain('Risk Flags:      NONE');
  });

  it('should display momentum metrics', () => {
    var lines = formatAnalyze(mockAnalyzeResult);
    var text = lines.join('\n');
    expect(text).toContain('72/100');
    expect(text).toContain('68/100');
    expect(text).toContain('Volume Surge:    YES');
    expect(text).toContain('ATR Expansion:   NO');
  });
});

describe('formatValuation', () => {
  it('should include ticker and sector in header', () => {
    var lines = formatValuation(mockValuationResult);
    var text = lines.join('\n');
    expect(text).toContain('VALUATION: ITC (FMCG)');
  });

  it('should display all valuation models', () => {
    var lines = formatValuation(mockValuationResult);
    var text = lines.join('\n');
    expect(text).toContain('Graham Number:');
    expect(text).toContain('PE-Relative:');
    expect(text).toContain('PEG Ratio:');
    expect(text).toContain('DCF Fair Value:');
  });

  it('should show above for CMP > Graham Number', () => {
    var lines = formatValuation(mockValuationResult);
    var text = lines.join('\n');
    expect(text).toContain('(above)');
  });

  it('should show below when CMP < Graham Number', () => {
    var belowResult = { ...mockValuationResult, cmp: 250 };
    var lines = formatValuation(belowResult);
    var text = lines.join('\n');
    expect(text).toContain('(below)');
  });

  it('should display UNDERVALUED verdict', () => {
    var lines = formatValuation(mockValuationResult);
    var text = lines.join('\n');
    expect(text).toContain('UNDERVALUED');
  });

  it('should show PEG ratio labels', () => {
    var lines = formatValuation(mockValuationResult);
    var text = lines.join('\n');
    expect(text).toContain('(fair)');
  });

  it('should display financial metrics', () => {
    var lines = formatValuation(mockValuationResult);
    var text = lines.join('\n');
    expect(text).toContain('P/E:');
    expect(text).toContain('28.5x');
    expect(text).toContain('ROE:');
    expect(text).toContain('28.0%');
  });

  it('should include disclaimer', () => {
    var lines = formatValuation(mockValuationResult);
    var text = lines.join('\n');
    expect(text).toContain('DISCLAIMER:');
    expect(text).toContain('SEBI-registered advisor');
  });
});

describe('formatRisk', () => {
  it('should include ticker in header', () => {
    var lines = formatRisk(mockRiskResult);
    var text = lines.join('\n');
    expect(text).toContain('RISK ANALYSIS: ITC');
  });

  it('should display all risk metrics', () => {
    var lines = formatRisk(mockRiskResult);
    var text = lines.join('\n');
    expect(text).toContain('Total Return:');
    expect(text).toContain('Annual Return:');
    expect(text).toContain('Volatility:');
    expect(text).toContain('Beta:');
    expect(text).toContain('VaR (95%):');
    expect(text).toContain('VaR (99%):');
    expect(text).toContain('Max Drawdown:');
    expect(text).toContain('Sharpe Ratio:');
    expect(text).toContain('Sortino Ratio:');
  });

  it('should show correct risk score label', () => {
    var lines = formatRisk(mockRiskResult);
    var text = lines.join('\n');
    expect(text).toContain('MED');
    expect(text).toContain('45/100');
    expect(text).toContain('Moderate');
  });

  it('should show positive return sign', () => {
    var lines = formatRisk(mockRiskResult);
    var text = lines.join('\n');
    expect(text).toContain('+15.5%');
  });

  it('should show negative return without plus sign', () => {
    var negRisk = { ...mockRiskResult, total_return: -8.2 };
    var lines = formatRisk(negRisk);
    var text = lines.join('\n');
    expect(text).toContain('-8.2%');
  });

  it('should include disclaimer', () => {
    var lines = formatRisk(mockRiskResult);
    var text = lines.join('\n');
    expect(text).toContain('DISCLAIMER:');
    expect(text).toContain('historical data');
  });
});

describe('formatBacktest', () => {
  it('should include ticker and strategy in header', () => {
    var lines = formatBacktest(mockBacktestResult);
    var text = lines.join('\n');
    expect(text).toContain('BACKTEST: ITC (triple-ema-crossover)');
  });

  it('should display period dates', () => {
    var lines = formatBacktest(mockBacktestResult);
    var text = lines.join('\n');
    expect(text).toContain('2023-01-01');
    expect(text).toContain('2024-01-01');
  });

  it('should display all summary metrics', () => {
    var lines = formatBacktest(mockBacktestResult);
    var text = lines.join('\n');
    expect(text).toContain('Starting Capital:');
    expect(text).toContain('Ending Capital:');
    expect(text).toContain('Total Return:');
    expect(text).toContain('CAGR:');
    expect(text).toContain('Max Drawdown:');
    expect(text).toContain('Win Rate:');
    expect(text).toContain('Profit Factor:');
    expect(text).toContain('Total Trades:');
    expect(text).toContain('Avg Holding:');
    expect(text).toContain('Risk:Reward:');
  });

  it('should show positive return with plus sign', () => {
    var lines = formatBacktest(mockBacktestResult);
    var text = lines.join('\n');
    expect(text).toContain('+15%');
  });

  it('should show recent trades with labels', () => {
    var lines = formatBacktest(mockBacktestResult);
    var text = lines.join('\n');
    expect(text).toContain('Recent Trades:');
    expect(text).toContain('WIN');
    expect(text).toContain('LOSS');
    expect(text).toContain('\u2713');
    expect(text).toContain('\u2717');
  });

  it('should include rupee symbol in trades', () => {
    var lines = formatBacktest(mockBacktestResult);
    var text = lines.join('\n');
    expect(text).toContain('\u20B9');
  });

  it('should not show Recent Trades section when no trades', () => {
    var noTrades = { ...mockBacktestResult, trades: [] };
    var lines = formatBacktest(noTrades);
    var text = lines.join('\n');
    expect(text).not.toContain('Recent Trades:');
  });

  it('should include disclaimer', () => {
    var lines = formatBacktest(mockBacktestResult);
    var text = lines.join('\n');
    expect(text).toContain('DISCLAIMER:');
    expect(text).toContain('Past backtest results');
  });
});

describe('formatScreenHeader', () => {
  it('should show header without sector filter', () => {
    var lines = formatScreenHeader();
    var text = lines.join('\n');
    expect(text).toContain('MOMENTUM SCREENER RESULTS');
    expect(text).toContain('Rank');
    expect(text).toContain('Ticker');
    expect(text).toContain('Sector');
    expect(text).toContain('Trend');
    expect(text).toContain('Mom. Score');
    expect(text).toContain('Risk Flags');
  });

  it('should show sector filter when provided', () => {
    var lines = formatScreenHeader('FMCG');
    var text = lines.join('\n');
    expect(text).toContain('Sector Filter: FMCG');
  });
});

describe('formatScreenRow', () => {
  it('should format stock data with alignment', () => {
    var row = formatScreenRow(0, mockScreenStocks[0]);
    expect(row).toContain('ITC');
    expect(row).toContain('FMCG');
    expect(row).toContain('72');
    expect(row).toContain('None');
  });

  it('should show risk flags when present', () => {
    var row = formatScreenRow(1, mockScreenStocks[1]);
    expect(row).toContain('RELIANCE');
    expect(row).toContain('High PE');
  });

  it('should display correct rank number', () => {
    var row = formatScreenRow(2, mockScreenStocks[0]);
    expect(row).toMatch(/^\s*3/);
  });
});

describe('formatCompareHeader', () => {
  it('should show comparison header with all columns', () => {
    var lines = formatCompareHeader();
    var text = lines.join('\n');
    expect(text).toContain('STOCK COMPARISON SCREEN');
    expect(text).toContain('Ticker');
    expect(text).toContain('Trend');
    expect(text).toContain('Mom. Score');
    expect(text).toContain('RS Score');
    expect(text).toContain('P/E');
    expect(text).toContain('Drawdown');
    expect(text).toContain('Flags');
  });
});

describe('formatCompareRow', () => {
  it('should format stock comparison data', () => {
    var row = formatCompareRow(mockCompareStocks[0]);
    expect(row).toContain('ITC');
    expect(row).toContain('72');
    expect(row).toContain('28.5x');
    expect(row).toContain('None');
  });

  it('should show N/A for null P/E', () => {
    var row = formatCompareRow(mockCompareStocks[1]);
    expect(row).toContain('RELIANCE');
    expect(row).toContain('N/A');
    expect(row).toContain('High Debt');
  });

  it('should display drawdown with negative sign', () => {
    var row = formatCompareRow(mockCompareStocks[0]);
    expect(row).toContain('-8.5%');
  });
});
