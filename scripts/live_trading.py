import logging
from datetime import datetime
from core.data.oanda_client import OandaDataClient
from core.strategies.momentum.rsi_momentum import RSIMomentumScalper
from services.execution.order_executor import OrderExecutor
from config import settings

class LiveTradingBot:
    def __init__(self):
        self.config = {
            'access_token': settings.OANDA_ACCESS_TOKEN,
            'account_id': settings.OANDA_ACCOUNT_ID,
            'environment': settings.OANDA_ENVIRONMENT,
            'redis_url': settings.REDIS_URL,
            'instrument': 'EUR_USD',
            'timeframe': 'M1'
        }
        
        self.data_client = OandaDataClient(self.config)
        self.strategy = RSIMomentumScalper(self.config)
        self.order_executor = OrderExecutor(self.config)
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Start live trading"""
        self.logger.info("Starting live trading bot")
        
        # Load initial data
        df = self.data_client.get_historical_candles(
            self.config['instrument'],
            self.config['timeframe'],
            count=100
        )
        
        # Start tick stream
        self.data_client.stream_ticks(
            self.config['instrument'],
            self._tick_handler
        )
        
    def _tick_handler(self, tick):
        """Process each incoming tick"""
        try:
            # Update latest price in DataFrame
            # In production, you'd maintain a proper rolling window
            new_row = {
                'time': tick['time'],
                'open': tick['bid'],
                'high': tick['bid'],
                'low': tick['bid'],
                'close': tick['bid'],
                'volume': tick['volume'],
                'spread': tick['spread']
            }
            
            # Generate features and signal
            features = self.strategy.calculate_features(df)
            signal = self.strategy.generate_signal(features)
            
            if signal['direction'] != 0:
                self.logger.info(f"Executing trade: {signal}")
                
                # Calculate position size based on risk
                stop_distance = abs(signal['entry'] - signal['stop_loss'])
                units = self.order_executor.calculate_position_size(stop_distance)
                
                # Execute order
                self.order_executor.create_order(
                    instrument=self.config['instrument'],
                    units=units * signal['direction'],
                    stop_loss=signal['stop_loss'],
                    take_profit=signal['take_profit'],
                    trailing_stop=signal['trailing_stop']
                )
                
        except Exception as e:
            self.logger.error(f"Error processing tick: {e}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bot = LiveTradingBot()
    bot.run()