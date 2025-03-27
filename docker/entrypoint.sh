#!/bin/bash

# Wait for Redis to be ready
until python -c "import redis; redis.Redis.from_url('$REDIS_URL').ping()"; do
  >&2 echo "Redis is unavailable - sleeping"
  sleep 1
done

# Run migrations or other pre-start commands
python scripts/initialize.py

# Start the main application
exec "$@"