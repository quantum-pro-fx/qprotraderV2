import oandapyV20
from oandapyV20.endpoints import instruments, orders, trades
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import redis
import json

class OandaDataClient:
    def __init__(self, config):
        self.client = oandapyV20.API(
            access_token=config['access_token'],
            environment=config['environment']
        )
        self.account_id = config['account_id']
        self.redis = redis.Redis.from_url(config['redis_url'])
        self.candle_cache_ttl = 3600  # 1 hour cache
        
    def get_historical_candles(self, instrument, timeframe, count, from_time=None):
        """Get historical candles with Redis caching"""
        cache_key = f"candles:{instrument}:{timeframe}:{count}"
        cached = self.redis.get(cache_key)
        
        if cached:
            return pd.DataFrame(json.loads(cached))
            
        params = {
            "granularity": timeframe,
            "count": count,
            "price": "BA"  # Bid/Ask prices
        }
        if from_time:
            params["from"] = from_time.isoformat() + "Z"
            
        r = instruments.InstrumentsCandles(
            instrument=instrument,
            params=params
        )
        candles = self.client.request(r)
        
        # Process to DataFrame
        data = []
        for c in candles['candles']:
            data.append({
                'time': pd.to_datetime(c['time']),
                'open': float(c['bid']['o']),
                'high': float(c['bid']['h']),
                'low': float(c['bid']['l']),
                'close': float(c['bid']['c']),
                'volume': int(c['volume']),
                'spread': float(c['ask']['c']) - float(c['bid']['c'])
            })
            
        df = pd.DataFrame(data)
        self.redis.setex(cache_key, self.candle_cache_ttl, json.dumps(df.to_dict(orient='records')))
        return df
        
    def stream_ticks(self, instrument, callback):
        """Stream real-time tick data"""
        params = {
            "instruments": instrument,
            "snapshot": True
        }
        r = instruments.InstrumentsStream(
            accountID=self.account_id,
            params=params
        )
        
        for tick in self.client.request(r):
            if 'tick' in tick:
                callback(self._process_tick(tick['tick']))
                
    def _process_tick(self, tick):
        """Process raw tick data for scalping"""
        return {
            'time': pd.to_datetime(tick['time']),
            'bid': float(tick['bid']),
            'ask': float(tick['ask']),
            'spread': float(tick['ask']) - float(tick['bid']),
            'volume': tick.get('volume', 0)
        }
    
    def get_account_summary(self):
        """Get account summary from OANDA"""
        endpoint = f"/v3/accounts/{self.account_id}/summary"
        r = accounts.AccountSummary(accountID=self.account_id)
        return self.client.request(r)