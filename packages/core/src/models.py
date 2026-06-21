from typing import List, Optional
from pydantic import BaseModel, Field

class StockSnapshot(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    exchange: str
    isin: str
    price: float
    open: float
    high: float
    low: float
    prev_close: float
    volume: int
    market_cap_cr: float
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: float = Field(..., alias="52w_high")
    fifty_two_week_low: float = Field(..., alias="52w_low")
    as_of: str

    class Config:
        populate_by_name = True

class OHLCV(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    delivery_pct: float

class Fundamentals(BaseModel):
    ticker: str
    revenue_growth_yoy: float
    profit_growth_yoy: float
    roce: float
    roe: float
    debt_to_equity: float
    free_cash_flow_cr: float
    earnings_acceleration: bool
    promoter_holding_pct: float
    promoter_pledge_pct: float
    fii_holding_pct: float
    dii_holding_pct: float
    public_holding_pct: float
    as_of_quarter: str

class TechnicalMetrics(BaseModel):
    ema_21: float
    ema_55: float
    ema_200: float
    price_vs_ema200_pct: float
    trend: str

class MomentumMetrics(BaseModel):
    rs_score: float
    rs_velocity: float
    volume_expansion: bool
    atr_expansion: bool
    momentum_score: float

class RiskMetrics(BaseModel):
    flags: List[str]
    atr_pct: float
    drawdown_from_52w_high_pct: float

class ValuationMetrics(BaseModel):
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None

class CompositeReport(BaseModel):
    ticker: str
    as_of: str
    source: str = "mock"
    technical: TechnicalMetrics
    momentum: MomentumMetrics
    risk: RiskMetrics
    valuation: ValuationMetrics
    disclaimer: str
