import os
import sqlite3
from typing import Optional

def get_db_path() -> str:
    # Resolve the database path dynamically
    # Start looking from current working directory or relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # We want it to be in nse-ai-agent/data/nse_platform.db
    # C:\laragon\www\nse-ai-agent\packages\core\src\db\connection.py
    # 4 levels up is packages/core
    # 5 levels up is root
    workspace_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    data_dir = os.path.join(workspace_root, "data")
    
    # Fallback to local data dir if workspace_root resolution seems off
    if not os.path.basename(workspace_root) == "nse-ai-agent" and not os.path.exists(data_dir):
        # try simple relative paths
        for rel in [".", "..", "../..", "../../..", "../../../.."]:
            test_dir = os.path.abspath(os.path.join(script_dir, rel, "data"))
            if os.path.exists(os.path.join(test_dir, "../package.json")) or os.path.basename(os.path.dirname(test_dir)) == "nse-ai-agent":
                data_dir = test_dir
                break
                
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "nse_platform.db")

def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    # Enable dict-like rows
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        ticker TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        sector TEXT NOT NULL,
        last_updated TEXT NOT NULL,
        raw_report TEXT
    )
    """)
    
    # Create agent_runs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_runs (
        run_id TEXT PRIMARY KEY,
        ticker TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        duration_ms INTEGER NOT NULL,
        success BOOLEAN NOT NULL,
        logs TEXT
    )
    """)
    
    # Create scores table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        score_type TEXT NOT NULL,
        value REAL NOT NULL,
        confidence REAL NOT NULL,
        computed_at TEXT NOT NULL,
        FOREIGN KEY (ticker) REFERENCES stocks (ticker)
    )
    """)
    
    # Create risk_flags table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        flag_type TEXT NOT NULL,
        description TEXT NOT NULL,
        computed_at TEXT NOT NULL,
        FOREIGN KEY (ticker) REFERENCES stocks (ticker)
    )
    """)
    
    conn.commit()
    conn.close()

# Run initialization on import
init_db()
