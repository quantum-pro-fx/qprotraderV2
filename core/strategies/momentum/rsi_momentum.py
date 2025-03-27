from core.strategies.base_strategy import BaseStrategy
import numpy as np

class RSIMomentumScalper(BaseStrategy):
    def generate_signal(self, features):
        signal = {
            'direction': 0,
            'entry': None,
            'stop_loss': None,
            'take_profit': None,
            'trailing_stop': None
        }
        
        # RSI Scalping logic
        rsi = features['rsi']
        spread = features['spread']
        
        if spread < 0.0002:  # Only trade when spread is tight
            if rsi < 30:
                signal['direction'] = 1  # Buy signal
            elif rsi > 70:
                signal['direction'] = -1  # Sell signal
                
        if signal['direction'] != 0:
            risk_params = self.calculate_risk_parameters(features)
            signal.update(risk_params)
            
        return signal