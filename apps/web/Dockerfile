FROM oven/bun:1.3-slim AS deps

WORKDIR /build

COPY package.json bun.lock nx.json tsconfig.base.json biome.json ./
COPY packages ./packages
COPY apps/web/package.json ./apps/web/

RUN bun install --frozen-lockfile

FROM deps AS build

ARG VITE_CLERK_PUBLISHABLE_KEY
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_CLERK_SIGN_IN_URL=/sign-in
ARG VITE_CLERK_SIGN_UP_URL=/sign-up
ARG VITE_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
ARG VITE_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/onboarding

ENV VITE_CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLISHABLE_KEY \
    VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_CLERK_SIGN_IN_URL=$VITE_CLERK_SIGN_IN_URL \
    VITE_CLERK_SIGN_UP_URL=$VITE_CLERK_SIGN_UP_URL \
    VITE_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=$VITE_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL \
    VITE_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=$VITE_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL \
    NODE_ENV=production

COPY apps/web ./apps/web

RUN bunx nx build @citetrack/web

FROM nginx:1.27-alpine AS production

COPY --from=build /build/apps/web/dist /usr/share/nginx/html

RUN cat <<'NGINX' > /etc/nginx/conf.d/default.conf
server {
    listen       8080;
    server_name  _;
    root         /usr/share/nginx/html;

    location ~* \.(?:js|css|woff2?|ttf|eot|svg|png|jpg|jpeg|gif|ico|webp|avif)$ {
        expires    1y;
        add_header Cache-Control "public, immutable";
        try_files  $uri =404;
    }

    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        expires    -1;
        try_files  $uri =404;
    }

    location / {
        add_header Cache-Control "no-cache" always;
        try_files $uri /index.html;
    }

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options        "DENY" always;
    add_header Referrer-Policy        "strict-origin-when-cross-origin" always;
}
NGINX

RUN chown -R nginx:nginx /usr/share/nginx/html \
 && chown -R nginx:nginx /var/cache/nginx \
 && chown -R nginx:nginx /var/log/nginx \
 && chown -R nginx:nginx /etc/nginx/conf.d \
 && touch /var/run/nginx.pid \
 && chown -R nginx:nginx /var/run/nginx.pid

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1:8080/favicon.svg || exit 1

CMD ["nginx", "-g", "daemon off;"]
