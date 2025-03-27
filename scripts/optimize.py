import optuna
from core.strategies.momentum.rsi_momentum import RSIMomentumScalper
from scripts.backtest import ScalpingBacktester
import pandas as pd
import logging

class ScalpingOptimizer:
    def __init__(self, data):
        self.data = data
        self.logger = logging.getLogger(__name__)

    def objective(self, trial):
        # Define search space
        params = {
            'rsi_period': trial.suggest_int('rsi_period', 5, 30),
            'rsi_lower': trial.suggest_int('rsi_lower', 10, 30),
            'rsi_upper': trial.suggest_int('rsi_upper', 70, 90),
            'atr_multiplier_sl': trial.suggest_float('atr_multiplier_sl', 0.5, 3.0),
            'atr_multiplier_tp': trial.suggest_float('atr_multiplier_tp', 0.5, 5.0),
            'max_spread': trial.suggest_float('max_spread', 0.0001, 0.0005)
        }
        
        # Run backtest with these parameters
        config = {
            'timeframe': 'T1',
            'strategy_params': params
        }
        
        backtester = ScalpingBacktester(config)
        _, metrics = backtester.run(self.data)
        
        # Optimize for Sharpe ratio
        return metrics['sharpe_ratio']
        
    def optimize(self, n_trials=100):
        study = optuna.create_study(direction='maximize')
        study.optimize(self.objective, n_trials=n_trials)
        
        self.logger.info(f"Best trial: {study.best_trial.value}")
        self.logger.info(f"Best params: {study.best_trial.params}")
        
        return study.best_trial.params

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Load your data
    data = pd.read_csv('tick_data.csv', parse_dates=['time'], index_col='time')
    
    optimizer = ScalpingOptimizer(data)
    best_params = optimizer.optimize(n_trials=50)
    print(f"Optimization complete. Best parameters: {best_params}")