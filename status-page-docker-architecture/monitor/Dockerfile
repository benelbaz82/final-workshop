# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the monitoring scripts
COPY cpu_monitor.py .
COPY ec2_monitor.py .

# Run the script based on SCRIPT env var, default to cpu_monitor
CMD ["sh", "-c", "python -u ${SCRIPT:-cpu_monitor}.py"]