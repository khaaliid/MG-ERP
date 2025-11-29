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

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
