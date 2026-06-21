from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict

class AgentState(TypedDict):
    ticker: str
    snapshot: Optional[Dict[str, Any]]
    ohlcv_data: Optional[List[Dict[str, Any]]]
    fundamentals: Optional[Dict[str, Any]]
    
    # Sub-agent outputs
    momentum_metrics: Optional[Dict[str, Any]]
    quality_metrics: Optional[Dict[str, Any]]
    ownership_metrics: Optional[Dict[str, Any]]
    
    # Final output report
    composite_report: Optional[Dict[str, Any]]
    
    # Execution records
    logs: List[str]
    errors: List[str]
    success: bool
    start_time: float
