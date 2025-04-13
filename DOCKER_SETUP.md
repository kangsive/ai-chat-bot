# Docker Setup for AI Chatbot Application

This document explains how to run both development and production Docker setups for the AI Chatbot application.

## Development Setup

The development setup is configured to provide a smooth development experience with hot-reloading and debugging capabilities.

### Running Development Environment

```bash
# Start the development stack
docker-compose up -d

# View logs
docker-compose logs -f
```

This setup:
- Mounts local code volumes for hot-reloading
- Uses development servers for both frontend and backend
- Exposes all ports for easy debugging
- Does not include a reverse proxy

## Production Setup

The production setup is optimized for performance, security, and reliability.

### Running Production Environment

```bash
# Create SSL certificates directory
mkdir -p nginx/ssl

# If using in production, replace with your real SSL certificates
# For testing, you can generate self-signed certificates:
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem -out nginx/ssl/fullchain.pem \
  -subj "/CN=yourdomain.com" \
  -addext "subjectAltName=DNS:yourdomain.com,DNS:www.yourdomain.com"

# Copy and customize the production environment file
cp .env.prod.example .env.prod
# Edit .env.prod with your production values

# Start the production stack
docker-compose -f docker-compose.prod.yml up -d

# Initialize the database (first time only)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Testing Production Environment

We provide a convenience script to test the production setup locally:

```bash
# Make the script executable
chmod +x test_prod.sh

# Run the test script
./test_prod.sh
```

This script:
- Creates self-signed SSL certificates for local testing
- Starts all production services
- Tests if the frontend and backend are responding correctly
- Provides detailed status information

### Production Features

The production setup includes:

1. **Nginx Reverse Proxy**:
   - SSL termination
   - Frontend & backend routing
   - HTTP to HTTPS redirection
   - WebSocket support for realtime features

2. **Backend Production Server**:
   - Uses Gunicorn with Uvicorn workers
   - Multiple worker processes for better performance
   - Optimized for production use

3. **Frontend**:
   - Running in development mode to handle CSS processing
   - Fully containerized setup

4. **Database**:
   - Persistent volume for data storage
   - Health checks to ensure readiness
   - Not exposed to the public internet

5. **Security Considerations**:
   - Container isolation
   - Non-root users where possible
   - SSL encryption
   - Environment variable separation

## Troubleshooting

### Common Issues

1. **Frontend CSS Processing Issues**:
   - The production setup uses the development server for the frontend to avoid CSS processing issues with Tailwind CSS.
   - If you need a true production build, you'll need to modify the frontend's Dockerfile.prod and ensure that all CSS processing tools are properly configured.

2. **Database Connection Issues**:
   - Make sure the database container is fully started before the backend attempts to connect.
   - Check the logs: `docker-compose -f docker-compose.prod.yml logs db`

3. **SSL Certificate Issues**:
   - Self-signed certificates will cause browser warnings - this is normal for local testing.
   - For production, use certificates from a trusted authority like Let's Encrypt.

### Viewing Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs

# View logs for a specific service
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs nginx
```

### Accessing Container Shell

```bash
docker-compose -f docker-compose.prod.yml exec backend bash
docker-compose -f docker-compose.prod.yml exec frontend sh
docker-compose -f docker-compose.prod.yml exec db bash
```

## Maintenance

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart containers
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backing Up the Database

```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres -d ai_chatbot > backup_$(date +%Y%m%d).sql
``` 