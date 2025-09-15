FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    git \
    postgresql-client \
    redis-tools \
    sed \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY ./status-page/requirements.txt .
RUN pip install --upgrade pip
RUN pip install rq-scheduler --force-reinstall
RUN pip install -r requirements.txt

# Copy the application code
COPY ./status-page/ .

# Make upgrade script executable
RUN chmod +x upgrade.sh

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set default environment variables (can be overridden)
ENV DEBUG=False
ENV DATABASE_NAME=statuspage
ENV DATABASE_USER=statuspage
ENV DATABASE_PASSWORD=statuspage123
ENV DATABASE_HOST=localhost
ENV DATABASE_PORT=5432
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379
ENV SECRET_KEY=change-this-in-production
ENV ALLOWED_HOSTS=localhost,127.0.0.1
ENV SITE_URL=http://localhost

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]