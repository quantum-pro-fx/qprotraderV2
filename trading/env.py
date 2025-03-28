import logging
from dataclasses import dataclass
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from data.models import Account
from brokers.base import IBroker
from config.settings import settings
from data.market_data import MarketData

logger = logging.getLogger(__name__)

@dataclass
class TradingEnv(gym.Env):
    def __init__(self, symbol: str, account: Account, broker: IBroker, market_data: MarketData):
        super().__init__()
        self.symbol = symbol
        self.account = account
        self.broker = broker
        self.market_data = market_data
        
        # Initialize position tracking (consistent naming)
        self.position_size = 0  # Use this name consistently
        self.entry_price = 0.0
        
        # Observation and action spaces
        self.observation_space = spaces.Dict({
            'mid_price': spaces.Box(0.0, np.inf, (1,), np.float32),
            'spread': spaces.Box(0.0, np.inf, (1,), np.float32),
            'volatility': spaces.Box(0.0, np.inf, (1,), np.float32),
            'momentum': spaces.Box(-np.inf, np.inf, (1,), np.float32),
            'liquidity': spaces.Box(0.0, 1.0, (1,), np.float32),
            'position_size': spaces.Box(-1.0, 1.0, (1,), np.float32),
            'pnl': spaces.Box(-np.inf, np.inf, (1,), np.float32)
        })

        self.action_space = spaces.Discrete(3)

    @property
    def observation_dim(self) -> int:
        """Calculate total flattened dimension"""
        return sum(np.prod(space.shape) for space in self.observation_space.spaces.values())

    async def reset(self):
        self.position_size = 0
        self.entry_price = 0.0
        return np.zeros(self.observation_space.shape, dtype=np.float32)
    
    async def step(self, action: int):
        # Validate action
        if action not in [0, 1, 2]:
            logger.error(f"Invalid action: {action}")
            return await self.reset()

        # Execute action - use position_size consistently
        if action == 1 and self.position_size <= 0:  # Buy signal
            quantity = self._calculate_position_size()
            order = await self.broker.place_order(
                self.account.account_id, 
                self.symbol, 
                "buy", 
                quantity
            )
            if order:
                self.position_size = quantity  # Changed from current_position
                self.entry_price = order.price
                
        elif action == 2 and self.position_size >= 0:  # Sell signal
            quantity = self._calculate_position_size()
            order = await self.broker.place_order(
                self.account.account_id, 
                self.symbol, 
                "sell", 
                quantity
            )
            if order:
                self.position_size = -quantity  # Changed from current_position
                self.entry_price = order.price
        
        # Get new observation
        state = await self._get_observation()
        reward = self._calculate_reward()
        done = False
        return state, reward, done, {}

    def _calculate_position_size(self) -> float:
        """Risk-managed position sizing"""
        max_risk = self.account.margin_available * settings.MAX_ACCOUNT_UTILIZATION
        return max_risk / (self.entry_price if self.entry_price > 0 else 1.0)
    
    def _calculate_reward(self) -> float:
        """Calculate PnL-based reward with risk adjustment"""
        if self.position_size == 0:
            return 0.0
            
        current_price = 1.0  # Would get from market data
        pnl = (current_price - self.entry_price) * self.position_size
        return pnl * 10000  # Scale to pips
    
    async def _get_observation(self) -> dict:
        """Get real market features"""
        features = self.market_data.get_features(self.symbol)
        if not features:
            return await self.reset()
            
        return {
            'mid_price': np.array([features['mid_price']], dtype=np.float32),
            'spread': np.array([features['spread']], dtype=np.float32),
            'volatility': np.array([features['volatility']], dtype=np.float32),
            'momentum': np.array([features['momentum']], dtype=np.float32),
            'liquidity': np.array([features['liquidity']], dtype=np.float32),
            'position_size': np.array([self.position_size / settings.DEFAULT_LOT_SIZE], dtype=np.float32),
            'pnl': np.array([self._calculate_pnl(features['mid_price'])], dtype=np.float32)
        }

    def _calculate_pnl(self, current_price: float) -> float:
        if self.position_size == 0:
            return 0.0
        return self.position_size * (current_price - self.entry_price)