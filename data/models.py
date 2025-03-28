from dataclasses import dataclass
from typing import Optional, List
import time

@dataclass
class Tick:
    symbol: str
    bid: float
    ask: float
    timestamp: float

@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    price: float
    quantity: float
    account_id: str
    timestamp: float

@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    account_id: str

@dataclass
class Account:
    account_id: str
    balance: float
    equity: float
    margin_available: float
    broker_name: str