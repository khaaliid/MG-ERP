FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
# Create .env with defaults if .env.docker is absent in CI
RUN echo "Preparing env file" && touch .env
COPY .env.docker .env
RUN if [ ! -s .env ]; then \
    echo "VITE_AUTH_BASE_URL=http://host.docker.internal:8004" >> .env && \
    echo "VITE_LEDGER_URL=http://localhost:3001" >> .env && \
    echo "VITE_INVENTORY_URL=http://localhost:3002" >> .env && \
    echo "VITE_POS_URL=http://localhost:3003" >> .env && \
    echo "VITE_AUTH_URL=http://localhost:3000" >> .env && \
    echo "VITE_PORTAL_URL=http://localhost:3005" >> .env ; \
  fi
COPY . .
RUN npm run build

FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf || true
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
