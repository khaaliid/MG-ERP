FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
RUN npm run build

FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf || true
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

# Environment variables for runtime configuration
ENV AUTH_SERVICE_URL=http://localhost:8004
ENV LEDGER_FRONTEND_URL=http://localhost:3001
ENV INVENTORY_FRONTEND_URL=http://localhost:3002
ENV POS_FRONTEND_URL=http://localhost:3003
ENV AUTH_FRONTEND_URL=http://localhost:3000
ENV PORTAL_FRONTEND_URL=http://localhost:3005

# Create entrypoint script to generate config.js at runtime
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'cat > /usr/share/nginx/html/config.js << EOF' >> /docker-entrypoint.sh && \
    echo 'window.APP_CONFIG = {' >> /docker-entrypoint.sh && \
    echo '  AUTH_BASE_URL: "${AUTH_SERVICE_URL}",' >> /docker-entrypoint.sh && \
    echo '  MODULE_AUTH_URL: "${AUTH_FRONTEND_URL}",' >> /docker-entrypoint.sh && \
    echo '  MODULE_LEDGER_URL: "${LEDGER_FRONTEND_URL}",' >> /docker-entrypoint.sh && \
    echo '  MODULE_INVENTORY_URL: "${INVENTORY_FRONTEND_URL}",' >> /docker-entrypoint.sh && \
    echo '  MODULE_POS_URL: "${POS_FRONTEND_URL}"' >> /docker-entrypoint.sh && \
    echo '};' >> /docker-entrypoint.sh && \
    echo 'EOF' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
ENTRYPOINT ["/docker-entrypoint.sh"]
