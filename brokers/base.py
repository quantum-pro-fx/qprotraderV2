from abc import ABC, abstractmethod
from typing import List, Optional
from data.models import Account, Order, Position, Tick

class IBroker(ABC):
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def get_accounts(self) -> List[Account]:
        pass
    
    @abstractmethod
    async def get_positions(self, account_id: str) -> List[Position]:
        pass
    
    @abstractmethod
    async def place_order(self, account_id: str, symbol: str, side: str, quantity: float) -> Optional[Order]:
        pass
    
    @abstractmethod
    async def stream_ticks(self, symbols: List[str], callback) -> None:
        pass

    @abstractmethod
    async def cancel_order(self, account_id: str, order_id: str) -> bool:
        pass