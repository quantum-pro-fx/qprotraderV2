import oandapyV20
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.positions import PositionClose
from oandapyV20.exceptions import V20Error
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self, config: Dict):
        self.client = oandapyV20.API(
            access_token=config["access_token"],
            environment=config["environment"]
        )
        self.account_id = config["account_id"]
    
    def execute_order(
        self,
        instrument: str,
        units: int,
        stop_loss: float,
        take_profit: float,
        trailing_stop: Optional[float] = None
    ) -> Dict:
        """Execute OANDA order with advanced risk controls."""
        order_payload = {
            "order": {
                "instrument": instrument,
                "units": str(units),
                "type": "MARKET",
                "stopLossOnFill": {
                    "price": str(round(stop_loss, 5)),
                    "timeInForce": "GTC"
                },
                "takeProfitOnFill": {
                    "price": str(round(take_profit, 5)),
                    "timeInForce": "GTC"
                }
            }
        }
        
        if trailing_stop:
            order_payload["order"]["trailingStopLossOnFill"] = {
                "distance": str(round(trailing_stop, 5)),
                "timeInForce": "GTC"
            }
        
        try:
            req = OrderCreate(accountID=self.account_id, data=order_payload)
            response = self.client.request(req)
            logger.info(f"Order executed: {response}")
            return response
        except V20Error as e:
            logger.error(f"OANDA order failed: {e}")
            return None
    
    def close_position(self, instrument: str) -> bool:
        """Force-close a position."""
        try:
            req = PositionClose(accountID=self.account_id, instrument=instrument)
            self.client.request(req)
            logger.info(f"Closed position for {instrument}")
            return True
        except V20Error as e:
            logger.error(f"Failed to close position: {e}")
            return False