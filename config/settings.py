import os
from dotenv import load_dotenv
import logging
from pathlib import Path

load_dotenv()

class Settings:
    # OANDA Configuration
    OANDA_API_KEY = os.getenv("OANDA_API_KEY")
    OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
    OANDA_ENVIRONMENT = os.getenv("OANDA_ENVIRONMENT", "practice")
    
    # Trading Parameters
    SYMBOLS = os.getenv("TRADING_PAIRS", "EUR_USD,GBP_USD,USD_JPY").split(",")
    MAX_ACCOUNT_UTILIZATION = float(os.getenv("MAX_ACCOUNT_UTILIZATION", 0.1))
    TARGET_LATENCY_MS = int(os.getenv("TARGET_LATENCY_MS", 50))
    INSTRUMENT_PRECISION = {
        'EUR_USD': 0,
        'GBP_USD': 0,
        'USD_JPY': 0,
        # Add other instruments as needed
    }

    # Trading Constants
    DEFAULT_LOT_SIZE = 1000  # Standard lot size in units
    MAX_SPREAD = 0.0003  # Maximum allowed spread (3 pips)

    # Logging Configuration
    LOG_DIR = Path("logs")
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def configure_logging(cls):
        cls.LOG_DIR.mkdir(exist_ok=True)
        logging.basicConfig(
            level=cls.LOG_LEVEL,
            format=cls.LOG_FORMAT,
            handlers=[
                logging.FileHandler(cls.LOG_DIR / "trading_bot.log"),
                logging.StreamHandler()
            ]
        )

settings = Settings()
settings.configure_logging()  # Initialize logging when settings are loaded