import pandas as pd
import numpy as np
from talib import abstract
from typing import Dict

class ScalpingFeatureEngine:
    def __init__(self, config):
        self.timeframe = config['timeframe']
        self.feature_window = config.get('feature_window', 50)
        
    def calculate_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate scalping-specific features"""
        features = {}
        
        # Price features
        features['spread'] = df['spread'].iloc[-1]
        features['spread_ma'] = df['spread'].rolling(5).mean().iloc[-1]
        
        # Microstructure features
        features['imbalance'] = self._calculate_order_imbalance(df)
        features['volatility'] = self._calculate_volatility(df)
        
        # TA features
        features['rsi'] = self._calculate_rsi(df)
        features['atr'] = self._calculate_atr(df)
        
        # Time features
        features['hour'] = df.index[-1].hour
        features['minute'] = df.index[-1].minute
        
        return features
        
    def _calculate_order_imbalance(self, df):
        """Calculate order book imbalance proxy"""
        price_change = df['close'].diff()
        volume_change = df['volume'].diff()
        return np.sign(price_change[-5:]).dot(volume_change[-5:]) / volume_change[-5:].sum()
        
    def _calculate_volatility(self, df):
        """Calculate short-term volatility"""
        returns = np.log(df['close']).diff()
        return returns.rolling(5).std().iloc[-1]
        
    def _calculate_rsi(self, df):
        """Calculate RSI for scalping"""
        inputs = {
            'open': df['open'].values,
            'high': df['high'].values,
            'low': df['low'].values,
            'close': df['close'].values,
            'volume': df['volume'].values
        }
        return abstract.RSI(inputs, timeperiod=14)[-1]
        
    def _calculate_atr(self, df):
        """Calculate ATR for stop placement"""
        inputs = {
            'high': df['high'].values,
            'low': df['low'].values,
            'close': df['close'].values
        }
        return abstract.ATR(inputs, timeperiod=14)[-1]