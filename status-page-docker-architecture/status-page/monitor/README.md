# CPU Monitor for Status-Page

This CPU monitor collects CPU usage data from the host system and sends it to a Status-Page instance via API.

## Overview

The monitor runs in a Docker container and:
- Monitors host CPU usage using `psutil`
- Sends data points to Status-Page metrics API
- Runs continuously with configurable intervals
- Requires access to host `/proc` filesystem for CPU data

## Prerequisites

- Docker and Docker Compose
- Status-Page instance running and accessible
- A configured metric in Status-Page to receive CPU data

## Status-Page Configuration

### 1. Create a Metric

1. Log into your Status-Page admin panel
2. Go to **Metrics** section
3. Click **Add Metric**
4. Configure the metric:
   - **Title**: "CPU Usage" or similar
   - **Suffix**: "%" (percentage symbol)
   - **Visibility**: Check to make it visible on status page
   - **Order**: Set display order (lower numbers appear first)
   - **Expand**: Choose when to show detailed data

### 2. Get API Token

1. In Status-Page admin panel, go to **Admin** > **Users**
2. Create or select a user for API access
3. Go to **Admin** > **Tokens**
4. Create a new token with appropriate permissions
5. Copy the token value for use in environment variables

### 3. Note the Metric ID

After creating the metric, note its ID from the URL or metric list. This will be used as `METRIC_ID` in the configuration.

## Running the Monitor

### Method 1: Using Docker Compose (Recommended)

1. Navigate to the monitor directory:
   ```bash
   cd status-page-docker-architecture/monitor
   ```

2. Run the monitor:
   ```bash
   docker-compose up -d
   ```

### Method 2: Using Docker Run

1. Build the image:
   ```bash
   docker build -t monitor:latest .
   ```

2. Run with required volume mount:
   ```bash
   docker run -d \
     --name cpu-monitor \
     -v /proc:/host/proc \
     -e METRIC_ID=1 \
     -e API_URL=http://host.docker.internal:8000/api/metrics/metric-points/ \
     -e API_TOKEN=your_api_token_here \
     -e INTERVAL=60 \
     monitor:latest
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `METRIC_ID` | ID of the metric in Status-Page | 1 | Yes |
| `API_URL` | Status-Page API endpoint URL | http://host.docker.internal:8000/api/metrics/metric-points/ | Yes |
| `API_TOKEN` | API token for authentication | YOUR_API_TOKEN | Yes |
| `INTERVAL` | Monitoring interval in seconds | 60 | No |

## Configuration File

The monitor can also be configured using a `.env` file in the parent directory:

```bash
# CPU Monitor Configuration
METRIC_ID=1
API_TOKEN=your_api_token_here
API_URL=http://host.docker.internal:8000/api/metrics/metric-points/
INTERVAL=60
```

## Troubleshooting

### Common Issues

1. **FileNotFoundError: [Errno 2] No such file or directory: '/host/proc/stat'**
   - **Cause**: Missing volume mount for host `/proc`
   - **Solution**: Ensure `-v /proc:/host/proc` is used when running the container

2. **Network is unreachable** or **Connection refused**
   - **Cause**: Status-Page API is not running or not accessible
   - **Solution**:
     - Ensure Status-Page is running on the expected host/port
     - Check `API_URL` configuration
     - For Docker setups, use `host.docker.internal` instead of `localhost`

3. **Authentication failed** or **403 Forbidden**
   - **Cause**: Invalid or missing API token
   - **Solution**:
     - Verify `API_TOKEN` is correct
     - Ensure the token has write permissions for metrics
     - Check token hasn't expired

4. **Metric not found** or **Invalid metric ID**
   - **Cause**: `METRIC_ID` doesn't match an existing metric
   - **Solution**: Verify the metric exists in Status-Page and note its correct ID

### Logs

View monitor logs:
```bash
# Using docker-compose
docker-compose logs -f cpu-monitor

# Using docker run
docker logs -f cpu-monitor
```

### Testing

Test the monitor manually:
```bash
# Run once to test
docker run --rm -v /proc:/host/proc -e METRIC_ID=1 -e API_URL=http://host.docker.internal:8000/api/metrics/metric-points/ -e API_TOKEN=your_token monitor:latest python -c "
import cpu_monitor
import time
cpu_monitor.get_cpu_usage()
print('CPU monitoring working!')
"
```

## Architecture

The monitor consists of:
- **cpu_monitor.py**: Main monitoring script
- **Dockerfile**: Container build configuration
- **docker-compose.yml**: Local development setup
- **requirements.txt**: Python dependencies

The monitor uses `psutil` to read CPU usage from `/host/proc/stat` and sends POST requests to the Status-Page API endpoint `/api/metrics/metric-points/` with the following JSON payload:

```json
{
  "metric": 1,
  "value": 45.2
}
```

## Security Notes

- The API token should be kept secure and not committed to version control
- The monitor requires host filesystem access (`/proc`) for CPU monitoring
- Consider using HTTPS for API communication in production
- Rotate API tokens regularly</content>
<parameter name="filePath">c:\Users\amitayb\Desktop\final-workshop\status-page-docker-architecture\monitor\README.md