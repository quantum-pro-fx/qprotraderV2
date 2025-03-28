import logging
import numpy as np
from collections import deque
from typing import Dict, Optional, List
from .models import Tick
from trading.rl.utils import check_for_nans

logger = logging.getLogger(__name__)

class MarketData:
    def __init__(self, symbols: List[str], window_size: int = 100):
        self.symbols = symbols
        self.window_size = window_size
        self.tick_data = {s: deque(maxlen=window_size) for s in symbols}
        self.features = {s: None for s in symbols}
        
    def update(self, tick: Tick) -> Optional[Dict]:
        """Main entry point that triggers feature calculation"""
        self.tick_data[tick.symbol].append(tick)
        return self._calculate_features(tick.symbol)

    def _calculate_features(self, symbol: str) -> Optional[Dict]:
        """PRIVATE method that actually computes the features"""
        ticks = list(self.tick_data[symbol])
        if len(ticks) < 20:  # Minimum data points
            return None

        bids = np.array([t.bid for t in ticks])
        asks = np.array([t.ask for t in ticks])

        self.features[symbol] = {
            'mid_price': (bids[-1] + asks[-1]) / 2,
            'spread': asks[-1] - bids[-1],
            'volatility': np.std(bids[-20:]),
            'momentum': bids[-1] - bids[-10],
            'liquidity': len(ticks) / self.window_size,
            'timestamp': ticks[-1].timestamp
        }
        return self.features[symbol]

    def get_features(self, symbol: str) -> Optional[dict]:
        """Public method to access features"""
        return self.features.get(symbol)
