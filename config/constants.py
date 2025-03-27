from enum import Enum, auto
import time

class Timeframe(Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"

class TradeAction(Enum):
    LONG = auto()
    SHORT = auto()
    HOLD = auto()

class TradingSession(Enum):
    LONDON = auto()
    NEW_YORK = auto()
    TOKYO = auto()
    SYDNEY = auto()

HIGH_VOLATILITY_PAIRS = [
    "EUR_USD", "GBP_USD", "USD_JPY",
    "AUD_USD", "USD_CAD", "NZD_USD",
    "EUR_JPY", "GBP_JPY", "XAU_USD"
]

class ConfigError(Exception):
    pass