import pandas as pd
import numpy as np
from core.strategies.momentum.rsi_momentum import RSIMomentumScalper
from core.data.feature_engine import ScalpingFeatureEngine
from services.execution.slippage import apply_slippage
from services.monitoring.performance import calculate_metrics
import logging

class ScalpingBacktester:
    def __init__(self, config):
        self.config = config
        self.strategy = RSIMomentumScalper(config)
        self.feature_engine = ScalpingFeatureEngine(config)
        self.logger = logging.getLogger(__name__)
        
    def run(self, data):
        """Run backtest on tick data"""
        results = []
        position = 0
        trade_history = []
        
        for i in range(50, len(data)):
            window = data.iloc[i-50:i]
            features = self.feature_engine.calculate_features(window)
            signal = self.strategy.generate_signal(features)
            
            if signal['direction'] != 0 and position == 0:
                # Execute trade
                entry_price = apply_slippage(
                    window.iloc[-1]['close'],
                    signal['direction'],
                    self.config.get('slippage', 0.0001)
                )
                
                trade = {
                    'entry_time': window.index[-1],
                    'entry_price': entry_price,
                    'direction': signal['direction'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'status': 'open'
                }
                trade_history.append(trade)
                position = signal['direction']
                
            # Check open trades
            for trade in [t for t in trade_history if t['status'] == 'open']:
                current_price = window.iloc[-1]['close']
                
                # Check stop loss
                if (trade['direction'] == 1 and current_price <= trade['stop_loss']) or \
                   (trade['direction'] == -1 and current_price >= trade['stop_loss']):
                    trade['exit_price'] = trade['stop_loss']
                    trade['exit_time'] = window.index[-1]
                    trade['status'] = 'closed'
                    position = 0
                    
                # Check take profit
                elif (trade['direction'] == 1 and current_price >= trade['take_profit']) or \
                     (trade['direction'] == -1 and current_price <= trade['take_profit']):
                    trade['exit_price'] = trade['take_profit']
                    trade['exit_time'] = window.index[-1]
                    trade['status'] = 'closed'
                    position = 0
                    
        # Calculate performance metrics
        metrics = calculate_metrics(trade_history)
        return trade_history, metrics
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Load sample data (replace with your data loading logic)
    data = pd.read_csv('tick_data.csv', parse_dates=['time'], index_col='time')
    
    config = {
        'timeframe': 'T1',  # Tick data
        'slippage': 0.0001,
        'max_trades': 100
    }
    
    backtester = ScalpingBacktester(config)
    trades, metrics = backtester.run(data)
    
    print(f"Backtest completed. Results: {metrics}")