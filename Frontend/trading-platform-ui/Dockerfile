# Multi-stage build for optimized production
FROM node:20-alpine as build

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm ci --only=production --silent && npm cache clean --force

# Copy source code
COPY . .

# Build arguments for API URL
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build with optimizations
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# Production stage with nginx for better performance
FROM nginx:alpine as production

# Copy custom nginx config
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
RUN echo 'server { \
    listen 3000; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass $REACT_APP_API_URL; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

# Development stage with hot reload
FROM node:20-alpine as development

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --silent

# Copy source code
COPY . .

EXPOSE 3000

# Enable hot reload
ENV WATCHPACK_POLLING=true
ENV FAST_REFRESH=true

CMD ["npm", "start"]