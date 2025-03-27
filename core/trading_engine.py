import logging
from typing import Dict, Optional
from core.data.oanda_client import OandaDataClient
from services.execution.order_executor import OrderExecutor
from core.risk.risk_manager import RiskManager
from core.strategies.base_strategy import BaseStrategy
from config import settings

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.data_client = OandaDataClient({
            "access_token": settings.OANDA_ACCESS_TOKEN,
            "account_id": settings.OANDA_ACCOUNT_ID,
            "environment": settings.OANDA_ENVIRONMENT,
            "redis_url": settings.REDIS_URL
        })
        self.order_executor = OrderExecutor({
            "access_token": settings.OANDA_ACCESS_TOKEN,
            "account_id": settings.OANDA_ACCOUNT_ID,
            "environment": settings.OANDA_ENVIRONMENT
        })
        self.risk_manager = RiskManager(settings.risk.dict())

    def run(self):
        """Main trading loop for scalping execution."""
        logger.info("Starting Trading Engine (Scalping Mode)")
        
        # Subscribe to real-time tick data
        self.data_client.stream_ticks(
            instrument=settings.INSTRUMENT,
            callback=self._process_tick
        )

    def _process_tick(self, tick_data: Dict):
        """Process each incoming tick for trading signals."""
        try:
            # 1. Generate features
            features = self.strategy.calculate_features(tick_data)
            
            # 2. Get trading signal
            signal = self.strategy.generate_signal(features)
            
            # 3. Validate risk
            if not self.risk_manager.validate_signal(signal):
                logger.warning("Signal blocked by risk manager")
                return
            
            # 4. Execute trade with OANDA
            if signal["action"] != "HOLD":
                self.order_executor.execute_order(
                    instrument=settings.INSTRUMENT,
                    units=signal["units"],
                    stop_loss=signal["stop_loss"],
                    take_profit=signal["take_profit"],
                    trailing_stop=signal.get("trailing_stop")
                )
                
        except Exception as e:
            logger.error(f"Error processing tick: {e}", exc_info=True)