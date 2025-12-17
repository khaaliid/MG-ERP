# Build stage
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Build-time environment for Vite
ARG VITE_API_BASE_URL=http://pos-backend:8001/api/v1
ARG VITE_AUTH_BASE_URL=http://auth:8004/api/v1/auth
RUN printf "VITE_API_BASE_URL=%s\nVITE_AUTH_BASE_URL=%s\n" "$VITE_API_BASE_URL" "$VITE_AUTH_BASE_URL" > .env

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
