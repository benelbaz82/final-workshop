# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the monitoring script
COPY cpu_monitor.py .

# Run the script with unbuffered output
CMD ["python", "-u", "cpu_monitor.py"]