FROM node:18-alpine

WORKDIR /app

# Copy package files and configuration files first for better layer caching
COPY package.json package-lock.json* ./
COPY postcss.config.js tailwind.config.js ./

# Install dependencies
RUN npm ci

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV development

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Run in development mode to avoid CSS processing issues
CMD ["npm", "run", "dev"] 