## Setting up Virtual Environment
python3 -m venv trading_env
source trading_env/bin/activate  # Linux/Mac
### OR
trading_env\Scripts\activate  # Windows

## Install packages
pip install -r requirements.txt

## Start Redis:
```
    docker-compose up -d
```

## Run live trading:
```
python scripts/live_trading.py
```

## For backtesting:
```
python scripts/backtest.py
```
## For optimization:
```
python scripts/optimize.py
```

Setup and Deployment Instructions
- Build the Docker images:
docker-compose -f docker/docker-compose.yml build

- Start the system:
docker-compose -f docker/docker-compose.yml up -d

- View logs:
docker logs -f scalping_bot

- Access Redis CLI:
docker exec -it scalping_redis redis-cli

- Make it executable:
chmod +x docker/entrypoint.sh

