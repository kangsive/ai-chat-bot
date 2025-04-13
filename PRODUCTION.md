# Production Deployment Guide

This guide explains how to deploy the AI Chatbot application to a production environment.

## Prerequisites

- Docker and Docker Compose installed on your server
- A domain name pointing to your server
- SSL certificates for your domain

## Setup Steps

1. **Prepare Environment Variables**

   ```bash
   cp .env.prod.example .env.prod
   ```

   Edit `.env.prod` and update all the values with your production settings.

2. **SSL Certificates**

   Place your SSL certificates in the `nginx/ssl` directory:
   
   ```bash
   mkdir -p nginx/ssl
   cp /path/to/your/fullchain.pem nginx/ssl/
   cp /path/to/your/privkey.pem nginx/ssl/
   ```

3. **Update Nginx Configuration**

   Edit `nginx/nginx.conf` and replace `yourdomain.com` with your actual domain name.

4. **Build and Start the Production Stack**

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Initialize the Database (First Time Only)**

   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

## Maintenance

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart containers
docker-compose -f docker-compose.prod.yml up -d --build
```

### Viewing Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs

# View logs for a specific service
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
```

### Backing Up the Database

```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres -d ai_chatbot_prod > backup_$(date +%Y%m%d).sql
```

## Security Considerations

1. Never expose the PostgreSQL port (5432) to the public internet
2. Regularly update your Docker images and dependencies
3. Keep your `.env.prod` file secure and never commit it to version control
4. Use strong passwords for all services
5. Consider implementing rate limiting for your API endpoints
6. Set up regular database backups

## Troubleshooting

### Checking Container Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Accessing Container Shell

```bash
docker-compose -f docker-compose.prod.yml exec backend bash
docker-compose -f docker-compose.prod.yml exec frontend sh
``` 