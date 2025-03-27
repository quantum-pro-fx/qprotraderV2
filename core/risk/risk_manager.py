import numpy as np
from datetime import datetime, time

class RiskManager:
    def __init__(self, config):
        self.max_daily_loss = config.get('max_daily_loss', 0.02)  # 2%
        self.max_position_size = config.get('max_position_size', 10000)
        self.max_trades_per_hour = config.get('max_trades_per_hour', 20)
        self.trade_count = 0
        self.last_trade_hour = None
        self.equity = config.get('initial_equity', 10000)
        
    def validate_order(self, instrument, units):
        """Check if order meets all risk criteria"""
        # Position size check
        if abs(units) > self.max_position_size:
            return False
            
        # Trading hour limits
        current_hour = datetime.now().hour
        if current_hour == self.last_trade_hour:
            if self.trade_count >= self.max_trades_per_hour:
                return False
        else:
            self.trade_count = 0
            self.last_trade_hour = current_hour
            
        # Don't trade during major news events (implement your own news filter)
        if self.is_news_event():
            return False
            
        return True
        
    def update_equity(self, pnl):
        """Update equity and check daily loss"""
        self.equity += pnl
        if self.equity <= (1 - self.max_daily_loss) * self.initial_equity:
            return False  # Stop trading for the day
        return True
        
    def is_news_event(self):
        """Implement your news event detection logic"""
        # Could integrate with services/sentiment/news_analyzer.py
        return False
        
    def calculate_position_size(self, stop_loss_pips):
        """Dynamic position sizing based on stop loss"""
        risk_per_trade = self.equity * 0.01  # Risk 1% per trade
        pip_value = 10  # For EUR/USD, adjust per instrument
        position_size = risk_per_trade / (stop_loss_pips * pip_value)
        return min(position_size, self.max_position_size)