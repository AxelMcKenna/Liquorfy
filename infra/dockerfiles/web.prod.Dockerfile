FROM node:22-alpine AS builder

WORKDIR /app/web

COPY web/package.json web/package-lock.json ./

RUN npm ci

COPY web ./

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/web/dist /usr/share/nginx/html
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
