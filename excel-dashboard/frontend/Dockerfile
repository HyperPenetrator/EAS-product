FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage — serve with Nginx
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config: pure static file server.
RUN echo 'server { listen 80; root /usr/share/nginx/html; index index.html; location / { try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["sh", "-c", "sed -i 's/listen 80;/listen '\"${PORT:-80}\"';/g' /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
