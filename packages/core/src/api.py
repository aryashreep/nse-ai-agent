import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Setup python path to find modules in packages/core/src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.mock_provider import MockProvider
from analysis.engine import AnalysisEngine
from agents.workflow import run_agent_pipeline
from db.operations import get_cached_report, save_composite_report, get_screened_momentum_from_db
from models import CompositeReport
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="NSE Agentic Research Platform API",
    description="Core analysis API for Indian stock markets.",
    version="1.0.0"
)

# Instrument the FastAPI app on startup to expose /metrics
Instrumentator().instrument(app).expose(app)

# Enable CORS for Next.js web application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize provider and engine for metadata checks
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.abspath(os.path.join(script_dir, "../../../data/mock/market_data.json"))
provider = MockProvider(data_file=data_path)
engine = AnalysisEngine(provider)

class AnalyzeRequest(BaseModel):
    ticker: str

class ScreenRequest(BaseModel):
    strategy: str = "momentum"
    sector: Optional[str] = None

class CompareRequest(BaseModel):
    tickers: List[str]

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/analyze", response_model=CompositeReport)
def analyze(req: AnalyzeRequest):
    try:
        ticker = req.ticker.upper().strip()
        
        # Verify ticker existence first
        try:
            provider.get_stock(ticker)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
            
        # Check cache
        report = get_cached_report(ticker)
        
        if report is None:
            # Execute LangGraph Agent workflow
            report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
            # Save to DB cache
            save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
            
        return report
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/screen")
def screen(req: ScreenRequest):
    try:
        if req.strategy != "momentum":
            raise HTTPException(status_code=400, detail="Only 'momentum' strategy is supported in Phase 2.")
        
        # Query cache
        screened = get_screened_momentum_from_db(sector=req.sector)
        
        # Calculate expected number of tickers for this sector or full universe
        expected_count = 20
        if req.sector:
            expected_count = len([t for t in provider.get_all_tickers() if provider.get_stock(t).sector.upper().strip() == req.sector.upper().strip()])
            
        # If cache has fewer items than expected, warm the missing ones
        if len(screened) < expected_count:
            all_screened = engine.screen_momentum(sector=req.sector)
            for stock_data in all_screened:
                ticker = stock_data["ticker"]
                try:
                    report = get_cached_report(ticker)
                    if report is None:
                        report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
                        save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
                except Exception:
                    pass
            
            # Query again from database to get fresh populated rows
            screened = get_screened_momentum_from_db(sector=req.sector)
            
        return screened
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screening failed: {str(e)}")

@app.post("/compare")
def compare(req: CompareRequest):
    try:
        reports = []
        for t in req.tickers:
            ticker = t.upper().strip()
            try:
                # Verify ticker existence
                provider.get_stock(ticker)
                
                # Check cache
                report = get_cached_report(ticker)
                if report is None:
                    report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
                    save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
                reports.append(report)
            except ValueError as e:
                reports.append({
                    "ticker": ticker,
                    "error": "NotFoundError",
                    "message": str(e)
                })
            except Exception as e:
                reports.append({
                    "ticker": ticker,
                    "error": "AnalysisError",
                    "message": str(e)
                })
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
