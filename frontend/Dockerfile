# syntax=docker/dockerfile:1

# ---------- stage 1: dependencies ----------
FROM node:20-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
# `npm ci` when a lockfile is present, otherwise a plain install.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi


# ---------- stage 2: build ----------
FROM node:20-alpine AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* is inlined into the client bundle, so it must exist at build time.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
ARG NEXT_PUBLIC_DEFAULT_LOCALE=en
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_PUBLIC_DEFAULT_LOCALE=$NEXT_PUBLIC_DEFAULT_LOCALE \
    NEXT_TELEMETRY_DISABLED=1

RUN npm run build


# ---------- stage 3: runtime ----------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 --ingroup nodejs nextjs

# `output: standalone` emits a self-contained server with only the traced
# dependencies, so no dev packages and no npm install reach this stage.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 \
    CMD wget -q --spider http://127.0.0.1:3000/healthz || exit 1

CMD ["node", "server.js"]
