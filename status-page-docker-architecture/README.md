# Status-Page Docker Setup

This document outlines the setup and architecture for running the Status-Page application using Docker.

## Architecture

The application is composed of several services orchestrated by `docker-compose`:

- **`nginx`**: Acts as a reverse proxy, directing traffic to the `web` service. It also serves static files directly for better performance.
- **`web`**: The main Status-Page application, a Django project running with Gunicorn. It handles all the application logic and API requests.
- **`postgres`**: A PostgreSQL database used as the primary data store for the application.
- **`redis`**: An in-memory data store, used by the application for caching and as a message broker for background tasks.
- **`scheduler`**: A service that schedules recurring tasks for the application.
- **`worker`**: A service that processes background jobs from a queue (e.g., sending notifications).

## Environment Variables

You can customize the superuser credentials using these environment variables in `docker-compose.yml`:

- `SUPERUSER_USERNAME`: Username for the admin user (default: `admin`)
- `SUPERUSER_EMAIL`: Email for the admin user (default: `admin@example.com`)
- `SUPERUSER_PASSWORD`: Password for the admin user (default: `admin123`)

## Current Credentials

**Username:** `admin`  
**Password:** `admin123`  
**Email:** `admin@example.com`

## Accessing the Application

1. The application runs on `http://localhost`
2. Go to `http://localhost/dashboard/login/` to log in
3. Use the credentials above to access the admin panel

## Commands

```bash
# Start the application
docker-compose up

# Stop the application
docker-compose down

# Rebuild and restart
docker-compose up --build

# View logs
docker-compose logs app

# Access Django shell
docker-compose exec app python3 statuspage/manage.py shell
```</content>
<parameter name="filePath">c:\Users\amitayb\Desktop\final test\README.md