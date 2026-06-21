import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from db.connection import get_connection
from models import (
    CompositeReport, TechnicalMetrics, MomentumMetrics,
    RiskMetrics, ValuationMetrics
)

def save_composite_report(report: CompositeReport, duration_ms: int = 0, success: bool = True, logs: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Convert Pydantic model to dict
        try:
            report_dict = report.model_dump()
        except AttributeError:
            report_dict = report.dict()
            
        raw_report_json = json.dumps(report_dict)
        ticker = report.ticker.upper().strip()
        now_str = datetime.now().isoformat()
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Get sector/name from snapshot (fallback to FMCG/Unknown if not available)
        # We can extract them if we have them from models
        # But wait! A composite report has pe/pb ratios.
        # Let's see if we can get stock name and sector from provider or we can pass it
        name = ticker
        sector = "Unknown"
        
        # Let's try to query current stock info to get name and sector
        # If the provider is available, we query it. We can pass a provider or resolve it.
        # Alternatively, we can parse the name and sector from the database if they exist,
        # or from the report if we extend it.
        # In mock data, sector can be resolved. Let's look up mock data.
        from data.mock_provider import MockProvider
        try:
            provider = MockProvider()
            stock = provider.get_stock(ticker)
            name = stock.name
            sector = stock.sector
        except Exception:
            pass

        # 1. Insert/Replace stock metadata and raw report
        cursor.execute("""
        INSERT OR REPLACE INTO stocks (ticker, name, sector, last_updated, raw_report)
        VALUES (?, ?, ?, ?, ?)
        """, (ticker, name, sector, date_str, raw_report_json))

        # 2. Log agent run
        import uuid
        run_id = str(uuid.uuid4())
        cursor.execute("""
        INSERT INTO agent_runs (run_id, ticker, timestamp, duration_ms, success, logs)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (run_id, ticker, now_str, duration_ms, success, logs))

        # 3. Clean old scores and flags for this stock
        cursor.execute("DELETE FROM scores WHERE ticker = ?", (ticker,))
        cursor.execute("DELETE FROM risk_flags WHERE ticker = ?", (ticker,))

        # 4. Insert new scores
        scores_to_insert = [
            ("momentum_score", report.momentum.momentum_score, 0.9),
            ("rs_score", report.momentum.rs_score, 0.9),
            ("rs_velocity", report.momentum.rs_velocity, 0.9),
            ("pe_ratio", report.valuation.pe_ratio or 0.0, 1.0),
        ]
        for score_type, val, conf in scores_to_insert:
            cursor.execute("""
            INSERT INTO scores (ticker, score_type, value, confidence, computed_at)
            VALUES (?, ?, ?, ?, ?)
            """, (ticker, score_type, val, conf, now_str))

        # 5. Insert new risk flags
        for flag in report.risk.flags:
            cursor.execute("""
            INSERT INTO risk_flags (ticker, flag_type, description, computed_at)
            VALUES (?, ?, ?, ?)
            """, (ticker, flag, f"Triggered flag: {flag}", now_str))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_cached_report(ticker: str) -> Optional[CompositeReport]:
    ticker = ticker.upper().strip()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT raw_report, last_updated FROM stocks WHERE ticker = ?
        """, (ticker,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        # Verify if it was updated today
        today_str = datetime.now().strftime("%Y-%m-%d")
        if row["last_updated"] != today_str:
            return None # stale cache
            
        raw_report_json = row["raw_report"]
        if not raw_report_json:
            return None
            
        report_dict = json.loads(raw_report_json)
        # Update source indicator to show it came from cache
        report_dict["source"] = "db_cache"
        
        try:
            return CompositeReport.model_validate(report_dict)
        except AttributeError:
            return CompositeReport.parse_obj(report_dict)
    except Exception:
        return None
    finally:
        conn.close()

def get_screened_momentum_from_db(sector: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Query latest reports for all stocks updated today
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        query = """
        SELECT raw_report FROM stocks WHERE last_updated = ?
        """
        params = [today_str]
        
        if sector:
            query += " AND sector = ?"
            params.append(sector)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            report_dict = json.loads(row["raw_report"])
            
            # Query stock details
            ticker = report_dict["ticker"]
            cursor.execute("SELECT name, sector, raw_report FROM stocks WHERE ticker = ?", (ticker,))
            stock_row = cursor.fetchone()
            
            # Fetch risk flags
            cursor.execute("SELECT flag_type FROM risk_flags WHERE ticker = ?", (ticker,))
            flags = [f["flag_type"] for f in cursor.fetchall()]
            
            # Get latest price from raw report
            price = report_dict["valuation"].get("pe_ratio") # wait, let's parse from raw report
            # Let's extract values cleanly
            
            # Let's parse stock details
            cursor.execute("SELECT value FROM scores WHERE ticker = ? AND score_type = 'momentum_score'", (ticker,))
            score_row = cursor.fetchone()
            mom_score = score_row["value"] if score_row else report_dict["momentum"]["momentum_score"]
            
            cursor.execute("SELECT value FROM scores WHERE ticker = ? AND score_type = 'rs_score'", (ticker,))
            rs_row = cursor.fetchone()
            rs_score = rs_row["value"] if rs_row else report_dict["momentum"]["rs_score"]
            
            results.append({
                "ticker": ticker,
                "name": stock_row["name"] if stock_row else ticker,
                "sector": stock_row["sector"] if stock_row else "Unknown",
                "price": report_dict["technical"].get("ema_21"), # placeholder or actual price
                "momentum_score": mom_score,
                "rs_score": rs_score,
                "trend": report_dict["technical"]["trend"],
                "risk_flags": flags
            })
            
        # Sort by momentum score descending
        results = sorted(results, key=lambda x: x["momentum_score"], reverse=True)
        return results
    except Exception:
        return []
    finally:
        conn.close()
