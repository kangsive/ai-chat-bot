FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy app files
COPY . .

# Build app
RUN npm run build

# Expose the listening port
EXPOSE 3000

# Run app
CMD ["npm", "start"] 