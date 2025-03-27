# config/risk_parameters.py
from pydantic import BaseModel, PositiveFloat, PositiveInt

class RiskParameters(BaseModel):
    max_daily_loss: PositiveFloat = 0.02  # 2%
    max_trade_risk: PositiveFloat = 0.01  # 1% per trade
    max_position_size: PositiveInt = 10000
    max_trades_per_hour: PositiveInt = 30
    min_spread: PositiveFloat = 0.0001
    equity_protection_level: PositiveFloat = 0.8  # Stop trading at 80% of initial
    
    class Config:
        frozen = True  # Immutable config