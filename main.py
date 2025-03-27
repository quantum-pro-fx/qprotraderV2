import logging
from config import settings
from core.agents.ppo_agent import ScalpingPPOAgent
from core.environments.trading_env import TradingEnv

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log'),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Configuration
    config = {
        'access_token': settings.OANDA_ACCESS_TOKEN,
        'account_id': settings.OANDA_ACCOUNT_ID,
        'environment': settings.OANDA_ENVIRONMENT,
        'instrument': 'EUR_USD',
        'timeframe': 'M1',
        'initial_equity': 10000,
        'n_envs': 4
    }
    
    try:
        # Initialize and train agent
        agent = ScalpingPPOAgent(config)
        logger.info("Starting training...")
        agent.train(total_timesteps=1_000_000)
        
        # Save trained model
        agent.model.save("scalping_ppo_model")
        logger.info("Training completed and model saved")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()