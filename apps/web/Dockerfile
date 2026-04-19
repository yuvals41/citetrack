FROM oven/bun:1.3-alpine AS build

WORKDIR /build

COPY package.json bun.lock nx.json tsconfig.base.json biome.json ./
COPY packages ./packages
COPY apps/web ./apps/web

RUN bun install --frozen-lockfile

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
    VITE_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=$VITE_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL

RUN bunx nx build @citetrack/web


FROM node:22-alpine AS runtime

ENV NODE_ENV=production \
    PORT=3003 \
    HOST=0.0.0.0

WORKDIR /app

RUN adduser -D -u 1001 citetrack && chown citetrack:citetrack /app
USER citetrack

COPY --from=build --chown=citetrack:citetrack /build/apps/web/.output ./.output

EXPOSE 3003

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1:3003/favicon.svg || exit 1

CMD ["node", ".output/server/index.mjs"]
