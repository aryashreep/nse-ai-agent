const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface TechnicalMetrics {
  ema_21: number;
  ema_55: number;
  ema_200: number;
  price_vs_ema200_pct: number;
  trend: string;
}

export interface MomentumMetrics {
  rs_score: number;
  rs_velocity: number;
  volume_expansion: boolean;
  atr_expansion: boolean;
  momentum_score: number;
}

export interface RiskMetrics {
  flags: string[];
  atr_pct: number;
  drawdown_from_52w_high_pct: number;
}

export interface ValuationMetrics {
  pe_ratio: number | null;
  pb_ratio: number | null;
  dividend_yield: number | null;
}

export interface CompositeReport {
  ticker: string;
  as_of: string;
  source: string;
  technical: TechnicalMetrics;
  momentum: MomentumMetrics;
  risk: RiskMetrics;
  valuation: ValuationMetrics;
  disclaimer: string;
}

export interface ScreenedStock {
  ticker: string;
  name: string;
  sector: string;
  price: number | null;
  momentum_score: number;
  rs_score: number;
  trend: string;
  risk_flags: string[];
}

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const errorText = await res.text();
    let detail = "API request failed";
    try {
      const parsed = JSON.parse(errorText);
      detail = parsed.detail || detail;
    } catch {
      detail = errorText || detail;
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<{ status: string }> {
  return fetchJson<{ status: string }>(`${API_BASE_URL}/health`);
}

export async function analyzeStock(ticker: string): Promise<CompositeReport> {
  return fetchJson<CompositeReport>(`${API_BASE_URL}/analyze`, {
    method: "POST",
    body: JSON.stringify({ ticker }),
  });
}

export async function screenMomentum(sector?: string): Promise<ScreenedStock[]> {
  return fetchJson<ScreenedStock[]>(`${API_BASE_URL}/screen`, {
    method: "POST",
    body: JSON.stringify({ strategy: "momentum", sector: sector || null }),
  });
}

export async function compareStocks(tickers: string[]): Promise<any[]> {
  return fetchJson<any[]>(`${API_BASE_URL}/compare`, {
    method: "POST",
    body: JSON.stringify({ tickers }),
  });
}

const PREDICTOR_API_URL = process.env.NEXT_PUBLIC_PREDICTOR_API_URL || "http://127.0.0.1:8001";

export interface IndexInclusionPrediction {
  ticker: string;
  index: string;
  prob_3m: number;
  prob_6m: number;
  prob_12m: number;
  feature_importances: Record<string, number>;
  metrics: {
    avg_log_loss: number;
    avg_precision_at_5: number;
    avg_precision_at_10: number;
    avg_recall_at_10: number;
  };
  model_version: string;
  last_updated: string;
}

export async function getPredictInclusion(
  ticker: string,
  index: string = "nifty_500_momentum_50"
): Promise<IndexInclusionPrediction> {
  return fetchJson<IndexInclusionPrediction>(`${PREDICTOR_API_URL}/predict-inclusion`, {
    method: "POST",
    body: JSON.stringify({ ticker, index }),
  });
}

