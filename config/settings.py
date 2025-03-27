# config/settings.py
import os
from dotenv import load_dotenv
from pathlib import Path
from .risk_parameters import RiskParameters

class Settings:
    def __init__(self):
        load_dotenv()
        
        # Required settings
        self.OANDA_ACCESS_TOKEN = self._get_env('OANDA_ACCESS_TOKEN')
        self.OANDA_ACCOUNT_ID = self._get_env('OANDA_ACCOUNT_ID')
        self.REDIS_URL = self._get_env('REDIS_URL', 'redis://localhost:6379')
        
        # Optional settings with defaults
        self.ENVIRONMENT = os.getenv('OANDA_ENVIRONMENT', 'practice')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Risk management
        self.risk = RiskParameters()
        
        # Path setup
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / 'data'
        self.MODEL_DIR = self.BASE_DIR / 'models'
        
        self._validate()
    
    def _get_env(self, var_name, default=None):
        value = os.getenv(var_name, default)
        if value is None:
            raise ValueError(f"Missing required environment variable: {var_name}")
        return value
    
    def _validate(self):
        if not self.DATA_DIR.exists():
            self.DATA_DIR.mkdir()
        if not self.MODEL_DIR.exists():
            self.MODEL_DIR.mkdir()

settings = Settings()