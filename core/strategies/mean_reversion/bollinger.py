import numpy as np
from core.strategies.base_strategy import BaseStrategy

class BollingerScalper(BaseStrategy):
    def generate_signal(self, features, window=20, num_std=2):
        signal = {
            'direction': 0,
            'entry': None,
            'stop_loss': None,
            'take_profit': None,
            'trailing_stop': None
        }
        
        # Calculate Bollinger Bands if not in features
        if 'upper_band' not in features or 'lower_band' not in features:
            rolling_mean = features['close'].rolling(window=window).mean()
            rolling_std = features['close'].rolling(window=window).std()
            upper_band = rolling_mean + (rolling_std * num_std)
            lower_band = rolling_mean - (rolling_std * num_std)
        else:
            upper_band = features['upper_band']
            lower_band = features['lower_band']
            
        current_price = features['close'][-1]
        
        if current_price <= lower_band[-1] and features['spread'] < 0.0003:
            signal['direction'] = 1  # Buy signal
        elif current_price >= upper_band[-1] and features['spread'] < 0.0003:
            signal['direction'] = -1  # Sell signal
            
        if signal['direction'] != 0:
            risk_params = self.calculate_risk_parameters(features)
            signal.update(risk_params)
            
        return signal