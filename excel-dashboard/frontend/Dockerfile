FROM node:20-alpine AS builder

ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage — serve with Nginx as non-root
FROM nginxinc/nginx-unprivileged:alpine AS production

# Copy static assets with correct ownership
COPY --chown=nginx:nginx --from=builder /app/dist /usr/share/nginx/html

# Copy the custom nginx template (unprivileged nginx automatically populates /etc/nginx/conf.d/default.conf from it on startup)
COPY --chown=nginx:nginx default.conf.template /etc/nginx/templates/default.conf.template

# Default fallback if PORT is not set
ENV PORT=8080

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
