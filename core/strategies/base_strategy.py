from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseStrategy(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    def generate_signal(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Generate trading signal with risk parameters"""
        pass
        
    def calculate_risk_parameters(self, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate dynamic stop loss/take profit"""
        atr = features.get('atr', 0.001)
        return {
            'stop_loss': features['close'] - 1.5 * atr,
            'take_profit': features['close'] + 2 * atr,
            'trailing_stop': 0.5 * atr
        }