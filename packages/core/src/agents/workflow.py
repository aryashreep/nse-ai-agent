import time
import os
import sys
from typing import Dict, Any, Tuple, List
from langgraph.graph import StateGraph, END

# Add parent path to search core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import AgentState
from models import (
    CompositeReport, TechnicalMetrics, MomentumMetrics,
    RiskMetrics, ValuationMetrics
)
from data.mock_provider import MockProvider
from analysis.engine import AnalysisEngine

# Standard Provider and Engine resolution
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.abspath(os.path.join(script_dir, "../../../../data/mock/market_data.json"))
provider = MockProvider(data_file=data_path)
engine = AnalysisEngine(provider)

# Node 1: scan_market
def scan_market(state: AgentState) -> Dict[str, Any]:
    ticker = state["ticker"].upper().strip()
    logs = list(state.get("logs", []))
    errors = list(state.get("errors", []))
    
    logs.append(f"MarketScannerAgent: Initiating market data scan for {ticker}...")
    
    try:
        stock = provider.get_stock(ticker)
        history = provider.get_history(ticker, 250)
        fundamentals = provider.get_fundamentals(ticker)
        
        # Convert Pydantic models to dicts to pass in LangGraph state
        try:
            snapshot_dict = stock.model_dump()
            fundamentals_dict = fundamentals.model_dump()
        except AttributeError:
            snapshot_dict = stock.dict()
            fundamentals_dict = fundamentals.dict()
            
        ohlcv_dicts = [h.model_dump() if hasattr(h, 'model_dump') else h.dict() for h in history]
        
        logs.append(f"MarketScannerAgent: Successfully retrieved profile snapshot, {len(history)} daily bars, and quarterly fundamentals.")
        return {
            "snapshot": snapshot_dict,
            "ohlcv_data": ohlcv_dicts,
            "fundamentals": fundamentals_dict,
            "logs": logs,
            "errors": errors
        }
    except Exception as e:
        error_msg = f"Failed to retrieve data for {ticker}: {str(e)}"
        logs.append(f"MarketScannerAgent ERROR: {error_msg}")
        errors.append(error_msg)
        return {
            "logs": logs,
            "errors": errors,
            "success": False
        }

# Node 2: analyze_momentum
def analyze_momentum(state: AgentState) -> Dict[str, Any]:
    ticker = state["ticker"].upper().strip()
    logs = list(state.get("logs", []))
    errors = list(state.get("errors", []))
    
    if not state.get("snapshot"):
        return {"logs": logs}
        
    logs.append("MomentumAgent: Running technical and relative strength calculations...")
    
    try:
        # Run computations using AnalysisEngine logic
        report = engine.run_analysis(ticker)
        
        try:
            tech_dict = report.technical.model_dump()
            mom_dict = report.momentum.model_dump()
        except AttributeError:
            tech_dict = report.technical.dict()
            mom_dict = report.momentum.dict()
            
        logs.append(
            f"MomentumAgent: Trend identified as {report.technical.trend.upper()}. "
            f"Relative Strength (RS) Score: {report.momentum.rs_score}/100, Momentum Score: {report.momentum.momentum_score}/100."
        )
        return {
            "momentum_metrics": {
                "technical": tech_dict,
                "momentum": mom_dict
            },
            "logs": logs
        }
    except Exception as e:
        error_msg = f"Failed to compute momentum metrics: {str(e)}"
        logs.append(f"MomentumAgent ERROR: {error_msg}")
        errors.append(error_msg)
        return {"logs": logs, "errors": errors}

# Node 3: analyze_fundamentals
def analyze_fundamentals(state: AgentState) -> Dict[str, Any]:
    ticker = state["ticker"].upper().strip()
    logs = list(state.get("logs", []))
    errors = list(state.get("errors", []))
    
    if not state.get("fundamentals"):
        return {"logs": logs}
        
    logs.append("FundamentalAgent: Analyzing ROCE, ROE, debt to equity, and growth velocity...")
    
    try:
        report = engine.run_analysis(ticker)
        try:
            val_dict = report.valuation.model_dump()
        except AttributeError:
            val_dict = report.valuation.dict()
            
        logs.append(
            f"FundamentalAgent: Calculated P/E: {report.valuation.pe_ratio}x, "
            f"P/B: {report.valuation.pb_ratio}x, Dividend Yield: {report.valuation.dividend_yield}%."
        )
        return {
            "quality_metrics": {
                "valuation": val_dict,
                "roce": state["fundamentals"]["roce"],
                "roe": state["fundamentals"]["roe"],
                "debt_to_equity": state["fundamentals"]["debt_to_equity"]
            },
            "logs": logs
        }
    except Exception as e:
        error_msg = f"Failed to compute fundamental metrics: {str(e)}"
        logs.append(f"FundamentalAgent ERROR: {error_msg}")
        errors.append(error_msg)
        return {"logs": logs, "errors": errors}

# Node 4: analyze_ownership
def analyze_ownership(state: AgentState) -> Dict[str, Any]:
    ticker = state["ticker"].upper().strip()
    logs = list(state.get("logs", []))
    errors = list(state.get("errors", []))
    
    if not state.get("fundamentals"):
        return {"logs": logs}
        
    logs.append("OwnershipAgent: Checking promoter pledge, FII/DII holdings, and public float...")
    
    try:
        fund = state["fundamentals"]
        logs.append(
            f"OwnershipAgent: Holdings - Promoter: {fund['promoter_holding_pct']}%, "
            f"FII: {fund['fii_holding_pct']}%, DII: {fund['dii_holding_pct']}%."
        )
        return {
            "ownership_metrics": {
                "promoter_holding_pct": fund["promoter_holding_pct"],
                "promoter_pledge_pct": fund["promoter_pledge_pct"],
                "fii_holding_pct": fund["fii_holding_pct"],
                "dii_holding_pct": fund["dii_holding_pct"],
                "public_holding_pct": fund["public_holding_pct"]
            },
            "logs": logs
        }
    except Exception as e:
        error_msg = f"Failed to analyze ownership holdings: {str(e)}"
        logs.append(f"OwnershipAgent ERROR: {error_msg}")
        errors.append(error_msg)
        return {"logs": logs, "errors": errors}

# Node 5: aggregate_report
def aggregate_report(state: AgentState) -> Dict[str, Any]:
    ticker = state["ticker"].upper().strip()
    logs = list(state.get("logs", []))
    errors = list(state.get("errors", []))
    
    logs.append("SupervisorAgent: Aggregating agent outputs and building compliance CompositeReport...")
    
    try:
        # Fetch the complete calculated report from the engine
        report = engine.run_analysis(ticker)
        
        # Format tracing and logs into raw report structure
        try:
            report_dict = report.model_dump()
        except AttributeError:
            report_dict = report.dict()
            
        logs.append(f"SupervisorAgent: Successfully compiled report for {ticker} containing {len(report.risk.flags)} active risk flags.")
        return {
            "composite_report": report_dict,
            "logs": logs,
            "success": True
        }
    except Exception as e:
        error_msg = f"Failed to compile aggregated report: {str(e)}"
        logs.append(f"SupervisorAgent ERROR: {error_msg}")
        errors.append(error_msg)
        return {
            "logs": logs,
            "errors": errors,
            "success": False
        }

# Assemble LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("scan_market", scan_market)
workflow.add_node("analyze_momentum", analyze_momentum)
workflow.add_node("analyze_fundamentals", analyze_fundamentals)
workflow.add_node("analyze_ownership", analyze_ownership)
workflow.add_node("aggregate_report", aggregate_report)

workflow.set_entry_point("scan_market")

workflow.add_edge("scan_market", "analyze_momentum")
workflow.add_edge("analyze_momentum", "analyze_fundamentals")
workflow.add_edge("analyze_fundamentals", "analyze_ownership")
workflow.add_edge("analyze_ownership", "aggregate_report")
workflow.add_edge("aggregate_report", END)

# Compile graph
graph = workflow.compile()

def run_agent_pipeline(ticker: str) -> Tuple[CompositeReport, int, bool, str]:
    """
    Executes the sequential multi-agent LangGraph pipeline for a specific stock ticker.
    Returns: Tuple of (CompositeReport, duration_ms, success_bool, logs_str)
    """
    start_time = time.time()
    initial_state = {
        "ticker": ticker,
        "logs": ["SupervisorAgent: Initializing multi-agent graph run..."],
        "errors": [],
        "success": False,
        "start_time": start_time
    }
    
    # Run graph execution
    final_state = graph.invoke(initial_state)
    
    duration_ms = int((time.time() - start_time) * 1000)
    success = final_state.get("success", False)
    logs_str = "\n".join(final_state.get("logs", []))
    
    composite_report_dict = final_state.get("composite_report")
    if not composite_report_dict:
        # Compile error report if something went wrong
        raise ValueError(f"Agent pipeline failed for {ticker}. Errors: {final_state.get('errors')}")
        
    try:
        report = CompositeReport.model_validate(composite_report_dict)
    except AttributeError:
        report = CompositeReport.parse_obj(composite_report_dict)
        
    return report, duration_ms, success, logs_str
