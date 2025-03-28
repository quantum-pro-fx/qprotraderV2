import asyncio
from config.settings import settings
from brokers.oanda import OandaBroker
from data.market_data import MarketData
from trading.env import TradingEnv
from trading.rl.agent import PPODQNAgent
import logging

logger = logging.getLogger(__name__)

class ScalpingBot:
    def __init__(self):
        self.broker = OandaBroker()  # Initialize broker here
        self.market_data = MarketData(settings.SYMBOLS)
        self.agents = {}
        self.running = False
        
    async def initialize(self):
        """Initialize all components with proper error handling"""
        try:
            # Connect to broker first
            if not await self.broker.connect():
                raise ConnectionError("Failed to connect to broker")
            
            # Load accounts
            accounts = await self.broker.get_accounts()
            if not accounts:
                raise ValueError("No valid accounts found")

            # Initialize agents
            for account in accounts:
                for symbol in settings.SYMBOLS:
                    env = TradingEnv(
                        symbol=symbol,
                        account=account,
                        broker=self.broker,
                        market_data=self.market_data
                    )

                    # print(f"observation_space=====", env.observation_space)

                     # DEBUG: Print critical info
                    logger.debug(f"Env for {symbol} observation_space: {env.observation_space}")
                    logger.debug(f"Type: {type(env.observation_space)}")
                    logger.debug(f"Shape: {getattr(env.observation_space, 'shape', 'MISSING')}")

                    # Verify environment is properly initialized
                    if env.observation_space is None:
                        raise ValueError(f"Environment for {symbol} has no observation space")
                    
                    if not hasattr(env.observation_space, 'shape'):
                        raise RuntimeError(f"Invalid observation space for {symbol}")

                    self.agents[(account.account_id, symbol)] = PPODQNAgent(env)
            
            logger.info("Initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}", exc_info=True)
            return False
        
    async def run(self):
        """Main trading loop with proper resource management"""
        if not self.agents:
            logger.error("No agents initialized. Call initialize() first.")
            return
            
        self.running = True
        try:
            # Start market data stream
            stream_task = asyncio.create_task(
                self.broker.stream_ticks(settings.SYMBOLS, self.on_tick)
            )
            
            # Start RL training tasks
            training_tasks = [
                agent.train() for agent in self.agents.values()
            ]
            
            await asyncio.gather(stream_task, *training_tasks)
            
        except Exception as e:
            logger.error(f"Runtime error: {str(e)}", exc_info=True)
        finally:
            self.running = False
            await self.shutdown()
    
    async def on_tick(self, tick):
        """Process incoming ticks with validation"""
        if not self.running:
            return
            
        try:
            # Update market data and get features
            if self.market_data.update(tick):
                features = self.market_data.get_features(tick.symbol)
                if features:
                    # Notify relevant agents
                    for (account_id, symbol), agent in self.agents.items():
                        if symbol == tick.symbol:
                            await agent.process_tick(features)
        except Exception as e:
            logger.error(f"Tick processing error: {str(e)}", exc_info=True)
    
    async def shutdown(self):
        """Clean up resources"""
        logger.info("Shutting down...")
        if hasattr(self, 'broker'):
            await self.broker.disconnect()
        self.agents.clear()

async def main():
    bot = ScalpingBot()
    if await bot.initialize():
        try:
            await bot.run()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())