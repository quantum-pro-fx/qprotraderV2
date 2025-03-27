#!/usr/bin/env python3
import logging
import redis
from config import settings
from core.data.oanda_client import OandaDataClient
from core.data.feature_engine import ScalpingFeatureEngine
import time

def initialize_redis():
    """Initialize Redis with required data structures"""
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        
        # Create required Redis data structures
        if not r.exists('system:initialized'):
            # Create empty sorted sets for tick data
            instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY']  # Add your pairs
            for instrument in instruments:
                r.zadd(f"ticks:{instrument}", {'init': 0})
                r.delete(f"ticks:{instrument}")  # Remove initialization
            
            # Create strategy parameters hash
            strategy_params = {
                'rsi_period': '14',
                'atr_period': '14',
                'max_spread': '0.0002',
                'position_size': '0.01'
            }
            r.hmset('strategy:scalping:params', strategy_params)
            
            r.set('system:initialized', '1')
            logging.info("Redis initialization complete")
        else:
            logging.info("Redis already initialized")
            
        return True
        
    except Exception as e:
        logging.error(f"Redis initialization failed: {e}")
        return False

def warmup_feature_cache():
    """Pre-load feature calculations"""
    try:
        client = OandaDataClient({
            'access_token': settings.OANDA_ACCESS_TOKEN,
            'account_id': settings.OANDA_ACCOUNT_ID,
            'environment': settings.OANDA_ENVIRONMENT,
            'redis_url': settings.REDIS_URL
        })
        
        engine = ScalpingFeatureEngine({'timeframe': 'M1'})
        
        for pair in ['EUR_USD', 'GBP_USD']:  # Major pairs
            logging.info(f"Warming up cache for {pair}")
            data = client.get_historical_candles(pair, 'M1', 500)
            if not data.empty:
                # Calculate and cache features
                features = engine.calculate_features(data)
                logging.info(f"Cached initial features for {pair}")
                
        return True
        
    except Exception as e:
        logging.error(f"Feature warmup failed: {e}")
        return False

def check_oanda_connection():
    """Verify OANDA API connectivity"""
    try:
        client = OandaDataClient({
            'access_token': settings.OANDA_ACCESS_TOKEN,
            'account_id': settings.OANDA_ACCOUNT_ID,
            'environment': settings.OANDA_ENVIRONMENT,
            'redis_url': settings.REDIS_URL
        })
        
        # Simple API call to check connectivity
        account_info = client.get_account_summary()
        logging.info(f"OANDA connection OK. Balance: {account_info['balance']}")
        return True
        
    except Exception as e:
        logging.error(f"OANDA connection failed: {e}")
        return False

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Starting system initialization...")
    
    # Run initialization steps with retries
    max_retries = 3
    delay = 5
    
    for i in range(max_retries):
        try:
            if all([
                initialize_redis(),
                check_oanda_connection(),
                warmup_feature_cache()
            ]):
                logging.info("System initialization completed successfully")
                return True
                
        except Exception as e:
            logging.warning(f"Initialization attempt {i+1} failed: {e}")
            if i < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
    
    logging.error("System initialization failed after multiple attempts")
    return False

if __name__ == "__main__":
    main()