import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models import StockSnapshot, OHLCV, Fundamentals

class MarketDataProvider(ABC):
    @abstractmethod
    def get_stock(self, ticker: str) -> StockSnapshot:
        pass

    @abstractmethod
    def get_history(self, ticker: str, days: int) -> List[OHLCV]:
        pass

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> Fundamentals:
        pass


class MockProvider(MarketDataProvider):
    def __init__(self, data_file: str = None):
        if data_file is None:
            # Try standard paths relative to current workspace or script location
            possible_paths = [
                "data/mock/market_data.json",
                "../../../data/mock/market_data.json",
                "../../data/mock/market_data.json",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data/mock/market_data.json")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    data_file = path
                    break
            
            if not data_file:
                # Default fallback
                data_file = "data/mock/market_data.json"
                
        self.data_file = data_file
        self.data: Dict[str, Any] = {}
        self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        except Exception as e:
            raise FileNotFoundError(f"Could not load mock data file from {self.data_file}: {e}")

    def get_all_tickers(self) -> List[str]:
        return list(self.data.keys())

    def get_stock(self, ticker: str) -> StockSnapshot:
        ticker = ticker.upper().strip()
        if ticker not in self.data:
            raise ValueError(f"Ticker {ticker} not found in Mock data.")
        snapshot_dict = self.data[ticker]["snapshot"]
        return StockSnapshot.parse_obj(snapshot_dict)

    def get_history(self, ticker: str, days: int = 250) -> List[OHLCV]:
        ticker = ticker.upper().strip()
        if ticker not in self.data:
            raise ValueError(f"Ticker {ticker} not found in Mock data.")
        history_list = self.data[ticker]["history"]
        # Limit to the requested number of days (from the end of the history)
        history_slice = history_list[-days:] if days < len(history_list) else history_list
        return [OHLCV.parse_obj(h) for h in history_slice]

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        ticker = ticker.upper().strip()
        if ticker not in self.data:
            raise ValueError(f"Ticker {ticker} not found in Mock data.")
        fundamentals_dict = self.data[ticker]["fundamentals"]
        return Fundamentals.parse_obj(fundamentals_dict)
