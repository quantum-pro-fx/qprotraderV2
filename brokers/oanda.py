import logging
from typing import Optional, List
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.trades as trades
from config.settings import settings
from data.models import Account, Order, Position, Tick
from .base import IBroker
import asyncio
import time
from datetime import datetime
import dateutil.parser

logger = logging.getLogger(__name__)

class OandaBroker(IBroker):
    def __init__(self):
        self.client = API(access_token=settings.OANDA_API_KEY,
                         environment=settings.OANDA_ENVIRONMENT)
        self.connected = False
        logger.info("OandaBroker initialized")
        
    async def connect(self) -> bool:
        try:
            logger.debug("Connecting to OANDA API")
            acc = accounts.AccountDetails(settings.OANDA_ACCOUNT_ID)
            self.client.request(acc)
            self.connected = True
            logger.info("Successfully connected to OANDA API")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}", exc_info=True)
            return False
    
    async def get_accounts(self) -> List[Account]:
        try:
            logger.debug("Fetching account information")
            acc = accounts.AccountDetails(settings.OANDA_ACCOUNT_ID)
            response = self.client.request(acc)
            logger.info("Successfully retrieved account information")
            return [Account(
                account_id=response['account']['id'],
                balance=float(response['account']['balance']),
                equity=float(response['account']['NAV']),
                margin_available=float(response['account']['marginAvailable']),
                broker_name="OANDA"
            )]
        except Exception as e:
            logger.error(f"Failed to get accounts: {str(e)}", exc_info=True)
            return []

    async def get_positions(self, account_id: str) -> List[Position]:
        try:
            logger.debug(f"Fetching positions for account {account_id}")
            response = self.client.request(
                positions.OpenPositions(accountID=account_id))
            
            positions_list = [
                Position(
                    symbol=pos['instrument'],
                    quantity=float(pos['long']['units']) if float(pos['long']['units']) > 0 
                          else float(pos['short']['units']),
                    entry_price=float(pos['long']['averagePrice']) if float(pos['long']['units']) > 0 
                                else float(pos['short']['averagePrice']),
                    current_price=float(pos['long']['price']) if float(pos['long']['units']) > 0 
                                  else float(pos['short']['price']),
                    account_id=account_id
                )
                for pos in response['positions']
            ]
            logger.info(f"Found {len(positions_list)} open positions")
            return positions_list
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}", exc_info=True)
            return []

    async def place_order(self, account_id: str, symbol: str, side: str, quantity: float) -> Optional[Order]:
        try:
            # Round quantity to appropriate precision for the instrument
            # Major currency pairs typically allow 2 decimal places for units
            precision = settings.INSTRUMENT_PRECISION.get(symbol, 2)
            rounded_quantity = round(quantity, precision)
            
            logger.debug(f"Placing {side} order for {symbol} (Qty: {rounded_quantity})")
            order = {
                "order": {
                    "units": str(rounded_quantity) if side == "buy" else f"-{rounded_quantity}",
                    "instrument": symbol,
                    "type": "MARKET"
                }
            }
            
            req = orders.OrderCreate(account_id, data=order)
            response = self.client.request(req)
            
            order = Order(
                order_id=response['orderFillTransaction']['id'],
                symbol=symbol,
                side=side,
                price=float(response['orderFillTransaction']['price']),
                quantity=rounded_quantity,
                account_id=account_id,
                timestamp=time.time()
            )
            logger.info(f"Order executed: {order}")
            return order
        except oandapyV20.exceptions.V20Error as e:
            logger.error(f"Order rejected: {e.msg}")
            return None
        except Exception as e:
            logger.error(f"Order failed: {str(e)}", exc_info=True)
            return None

    async def cancel_order(self, account_id: str, order_id: str) -> bool:
        try:
            logger.debug(f"Cancelling order {order_id}")
            req = trades.TradeClose(account_id, order_id)
            self.client.request(req)
            logger.info(f"Successfully cancelled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}", exc_info=True)
            return False

    async def stream_ticks(self, symbols: List[str], callback):
        params = {"instruments": ",".join(symbols)}
        logger.info(f"Starting tick stream for symbols: {', '.join(symbols)}")
        
        while True:
            try:
                stream = pricing.PricingStream(accountID=settings.OANDA_ACCOUNT_ID,
                                            params=params)
                for tick in self.client.request(stream):
                    if 'type' in tick and tick['type'] == 'PRICE':
                        try:
                            # Robust timestamp parsing
                            timestamp_str = tick['time'].replace('Z', '+00:00')
                            try:
                                timestamp = dateutil.parser.isoparse(timestamp_str).timestamp()
                            except ValueError:
                                # Fallback for malformed timestamps
                                timestamp = time.time()
                                logger.warning(f"Using current time for malformed timestamp: {tick['time']}")
                            
                            tick_data = Tick(
                                symbol=tick['instrument'],
                                bid=float(tick['bids'][0]['price']),
                                ask=float(tick['asks'][0]['price']),
                                timestamp=timestamp
                            )
                            await callback(tick_data)
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Skipping malformed tick: {tick}. Error: {e}")
                            continue
            except Exception as e:
                logger.error(f"Stream error: {str(e)}. Reconnecting...", exc_info=True)
                await asyncio.sleep(1)