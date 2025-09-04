# Status-Page Docker Setup

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

1. The application runs on `http://localhost:8000`
2. Go to `http://localhost:8000/dashboard/login/` to log in
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