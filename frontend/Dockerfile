# Multi-stage build for Quasar frontend

# Stage 1: Build
FROM node:20-alpine as build

# Build arguments
ARG API_URL=http://localhost:8000
ARG PANEL_URL=http://localhost:5100

# Set as environment variables for build process
ENV API_URL=${API_URL}
ENV PANEL_URL=${PANEL_URL}

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build for production
RUN npm run build:pwa

# Stage 2: Production
FROM nginx:alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy built files
COPY --from=build /app/dist/pwa /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check - use curl which doesn't require temp files with -f flag
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost/ > /dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
