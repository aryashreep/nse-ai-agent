import sys
import os
import json
import argparse
from typing import List

# Setup python path to find modules in packages/core/src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.mock_provider import MockProvider
from analysis.engine import AnalysisEngine
from agents.workflow import run_agent_pipeline
from db.operations import get_cached_report, save_composite_report, get_screened_momentum_from_db

def parse_args():
    parser = argparse.ArgumentParser(description="NSE Agentic Research Platform Local Analyzer")
    subparsers = parser.add_subparsers(dest="command", help="Analysis commands")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a specific ticker")
    analyze_parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g. ITC)")

    # screen command
    screen_parser = subparsers.add_parser("screen", help="Screen for momentum opportunities")
    screen_parser.add_argument("strategy", type=str, nargs="?", default="momentum", help="Screening strategy (default: momentum)")
    screen_parser.add_argument("--sector", type=str, default=None, help="Filter by sector name")

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare multiple tickers")
    compare_parser.add_argument("tickers", type=str, nargs="+", help="List of stock ticker symbols")

    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        # Resolve path to mock data relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.abspath(os.path.join(script_dir, "../../../data/mock/market_data.json"))
        
        provider = MockProvider(data_file=data_path)
        engine = AnalysisEngine(provider)
    except Exception as e:
        print(json.dumps({
            "error": "InitializationError",
            "message": f"Failed to initialize data provider or engine: {str(e)}"
        }), file=sys.stderr)
        sys.exit(1)

    if args.command == "analyze":
        try:
            ticker = args.ticker.upper().strip()
            
            # Check SQLite database cache first
            report = get_cached_report(ticker)
            
            if report is None:
                # Cache miss: Execute LangGraph pipeline
                report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
                
                # Save to database
                save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
            
            # Print output
            try:
                print(report.model_dump_json())
            except AttributeError:
                print(report.json())
        except ValueError as e:
            print(json.dumps({
                "error": "NotFoundError",
                "message": str(e)
            }))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({
                "error": "AnalysisError",
                "message": f"An error occurred during analysis: {str(e)}"
            }))
            sys.exit(0)

    elif args.command == "screen":
        try:
            if args.strategy != "momentum":
                print(json.dumps({
                    "error": "UnsupportedStrategy",
                    "message": f"Strategy {args.strategy} is not supported. Use 'momentum'."
                }))
                sys.exit(0)
                
            # Read from DB first (if all tickers are updated today)
            screened = get_screened_momentum_from_db(sector=args.sector)
            
            # Calculate expected count
            expected_count = 20
            if args.sector:
                expected_count = len([t for t in provider.get_all_tickers() if provider.get_stock(t).sector.upper().strip() == args.sector.upper().strip()])
                
            # If cache has fewer items than expected, warm the missing ones
            if len(screened) < expected_count:
                all_screened = engine.screen_momentum(sector=args.sector)
                for stock_data in all_screened:
                    ticker = stock_data["ticker"]
                    try:
                        report = get_cached_report(ticker)
                        if report is None:
                            report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
                            save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
                    except Exception:
                        pass
                
                # Query again from database to return the formatted list
                screened = get_screened_momentum_from_db(sector=args.sector)
                
            print(json.dumps(screened))
        except Exception as e:
            print(json.dumps({
                "error": "ScreenError",
                "message": f"An error occurred during screening: {str(e)}"
            }))
            sys.exit(0)

    elif args.command == "compare":
        try:
            reports = []
            for t in args.tickers:
                ticker = t.upper().strip()
                try:
                    # Check cache first
                    report = get_cached_report(ticker)
                    if report is None:
                        # Execute LangGraph pipeline
                        report, duration_ms, success, logs_str = run_agent_pipeline(ticker)
                        save_composite_report(report, duration_ms=duration_ms, success=success, logs=logs_str)
                        
                    try:
                        reports.append(report.model_dump())
                    except AttributeError:
                        reports.append(report.dict())
                except ValueError as e:
                    reports.append({
                        "ticker": ticker,
                        "error": "NotFoundError",
                        "message": str(e)
                    })
            print(json.dumps(reports))
        except Exception as e:
            print(json.dumps({
                "error": "CompareError",
                "message": f"An error occurred during comparison: {str(e)}"
            }))
            sys.exit(0)
    else:
        # Default behavior: if no command is specified, print help
        print(json.dumps({
            "error": "UsageError",
            "message": "No command specified. Available commands: analyze, screen, compare"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
