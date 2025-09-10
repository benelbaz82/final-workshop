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
# Modified for scheduler fix
COPY ./status-page/ .

# Make upgrade script executable
RUN chmod +x upgrade.sh

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]