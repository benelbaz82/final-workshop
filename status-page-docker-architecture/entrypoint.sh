#!/bin/bash

export PGPASSWORD=$PGPASSWORD

# Wait for postgres to be ready
until pg_isready -h benami-postgres.cx248m4we6k7.us-east-1.rds.amazonaws.com -p 5432 -U statuspage_user; do
  echo "Waiting for postgres..."
  sleep 2
done

# Wait for redis to be ready
until redis-cli -h benami-redis.7fftml.ng.0001.use1.cache.amazonaws.com ping | grep -q PONG; do
  echo "Waiting for redis..."
  sleep 2
done

# Check if this is first run (no configuration.py exists) - only for web service
if [ "$SERVICE_NAME" = "web" ] && [ ! -f "statuspage/statuspage/configuration.py" ]; then
  echo "First run detected - performing initial setup..."

  # Copy configuration file
  echo "Creating configuration file..."
  cp statuspage/statuspage/configuration_example.py statuspage/statuspage/configuration.py

  # Update configuration with environment variables
  sed -i "s/'NAME': 'status-page'/'NAME': 'statuspage'/g" statuspage/statuspage/configuration.py
  sed -i "s/'USER': 'status-page'/'USER': 'statuspage'/g" statuspage/statuspage/configuration.py
  sed -i "s/'PASSWORD': 'abcdefgh123456'/'PASSWORD': '$PGPASSWORD'/g" statuspage/statuspage/configuration.py
  sed -i "s/'HOST': 'localhost'/'HOST': 'postgres'/g" statuspage/statuspage/configuration.py
  sed -i "s/'HOST': 'localhost',  # Redis server/'HOST': 'redis',  # Redis server/g" statuspage/statuspage/configuration.py
  sed -i "s/DEBUG = False/DEBUG = True/g" statuspage/statuspage/configuration.py
  sed -i "s/DEVELOPER = False/DEVELOPER = True/g" statuspage/statuspage/configuration.py

  # Generate secret key
  echo "Generating secret key..."
  SECRET_KEY=$(python3 statuspage/generate_secret_key.py)
  sed -i "s/SECRET_KEY = 'your_secret_key_here'/SECRET_KEY = '$SECRET_KEY'/g" statuspage/statuspage/configuration.py

  # Run upgrade script
  echo "Running upgrade script..."
  ./upgrade.sh

  echo "Initial setup completed!"
else
  echo "Configuration exists - skipping initial setup"
fi

# Always ensure superuser exists (in case database was reset) - only for web service
if [ "$SERVICE_NAME" = "web" ]; then
  echo "Ensuring superuser exists..."
  SUPERUSER_USERNAME=${SUPERUSER_USERNAME:-admin}
  SUPERUSER_EMAIL=${SUPERUSER_EMAIL:-admin@example.com}
  SUPERUSER_PASSWORD=${SUPERUSER_PASSWORD:-admin}

  cd statuspage

  # Run migrations first
  echo "Running migrations..."
  python3 manage.py makemigrations
  python3 manage.py migrate

  # Collect static files
  python3 manage.py collectstatic --no-input

  # Clear any existing cache
  python3 manage.py clearcache

  python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$SUPERUSER_USERNAME', '$SUPERUSER_EMAIL', '$SUPERUSER_PASSWORD')
    print('Superuser $SUPERUSER_USERNAME created')
else:
    print('Superuser $SUPERUSER_USERNAME already exists')
"

  # Build documentation (always needed)
  echo "Building documentation..."
  cd ..
  mkdocs build
  cd statuspage
fi

# Run the specific command based on service
case "$SERVICE_NAME" in
  "web")
    echo "Starting web service with Gunicorn..."
    export PYTHONPATH="/app/statuspage:$PYTHONPATH"
    exec gunicorn --config gunicorn.py --pythonpath /app/statuspage statuspage.wsgi
    ;;
  "scheduler")
    echo "Starting scheduler service..."
    cd statuspage
    export PYTHONPATH="/app/statuspage:$PYTHONPATH"
    exec python3 manage.py rqscheduler
    ;;
  "worker")
    echo "Starting worker service..."
    cd statuspage
    export PYTHONPATH="/app/statuspage:$PYTHONPATH"
    exec python3 manage.py rqworker high default low
    ;;
  *)
    echo "Unknown service: $SERVICE_NAME"
    exit 1
    ;;
esac