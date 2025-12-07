## Ledger Frontend Dockerfile
## Multi-stage build: Node (build) -> Nginx (serve)

FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency manifests first for better layer caching
COPY package*.json ./

# Install dependencies (prefer deterministic ci if lock present)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy Docker-specific env file if present
COPY .env.docker .env

# Copy source
COPY . .

# Build
RUN npm run build

FROM nginx:alpine

# Replace default config with SPA-friendly one
RUN rm /etc/nginx/conf.d/default.conf || true
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

# Environment variables for runtime configuration
ENV AUTH_SERVICE_URL=http://localhost:8004
ENV INVENTORY_SERVICE_URL=http://localhost:8002
ENV LEDGER_SERVICE_URL=http://localhost:8000
ENV POS_SERVICE_URL=http://localhost:8001

# Create entrypoint script to generate config.js at runtime
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'cat > /usr/share/nginx/html/config.js << EOF' >> /docker-entrypoint.sh && \
    echo 'window.APP_CONFIG = {' >> /docker-entrypoint.sh && \
    echo '  AUTH_BASE_URL: "${AUTH_SERVICE_URL}",' >> /docker-entrypoint.sh && \
    echo '  INVENTORY_BASE_URL: "${INVENTORY_SERVICE_URL}",' >> /docker-entrypoint.sh && \
    echo '  LEDGER_BASE_URL: "${LEDGER_SERVICE_URL}",' >> /docker-entrypoint.sh && \
    echo '  POS_BASE_URL: "${POS_SERVICE_URL}"' >> /docker-entrypoint.sh && \
    echo '};' >> /docker-entrypoint.sh && \
    echo 'EOF' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
