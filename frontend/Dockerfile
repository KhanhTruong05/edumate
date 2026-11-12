# Build context: repository root
FROM node:24-bookworm-slim AS build
WORKDIR /build/frontend
RUN npm install --global pnpm@11.25.0
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
ENV VITE_API_BASE=/api/v1
RUN pnpm build

FROM nginx:stable-alpine
COPY --from=build /build/frontend/dist/ /usr/share/nginx/html/
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/frontend-health || exit 1
