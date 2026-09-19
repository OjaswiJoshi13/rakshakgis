# ==============================================================================
# RakshakGIS Frontend Multi-Stage Production Dockerfile
# Framework: Next.js 14 (Standalone Output)
# Runtime: Node.js 20 Alpine (Unprivileged User: nextjs UID 1001)
# Build Context: ./frontend
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Installation
# ------------------------------------------------------------------------------
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies deterministically from committed lockfile
COPY package.json package-lock.json ./
RUN npm ci

# ------------------------------------------------------------------------------
# Stage 2: Application Build
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Internal backend URL used for Next.js server-side API proxy rewrites
ARG BACKEND_INTERNAL_URL=http://backend:8000
ENV BACKEND_INTERNAL_URL=$BACKEND_INTERNAL_URL

# Public environment variables inlined into client bundle at build time
ARG NEXT_PUBLIC_API_BASE_URL=/api/v1
ARG NEXT_PUBLIC_DATA_MODE=demo
ARG NEXT_PUBLIC_ACTIVE_REGION=himalayan_pilot
ARG NEXT_PUBLIC_MAP_STYLE_URL=https://demotiles.maplibre.org/style.json
ARG NEXT_PUBLIC_APP_VERSION=0.1.0

ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_DATA_MODE=$NEXT_PUBLIC_DATA_MODE
ENV NEXT_PUBLIC_ACTIVE_REGION=$NEXT_PUBLIC_ACTIVE_REGION
ENV NEXT_PUBLIC_MAP_STYLE_URL=$NEXT_PUBLIC_MAP_STYLE_URL
ENV NEXT_PUBLIC_APP_VERSION=$NEXT_PUBLIC_APP_VERSION

# Build Next.js with standalone output
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 3: Minimal Production Runtime
# ------------------------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create unprivileged system group and user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy runtime configuration and entrypoint scripts
COPY --chown=nextjs:nodejs configure-runtime.js /app/configure-runtime.js
COPY --chown=nextjs:nodejs docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Copy static assets and standalone server output
COPY --from=builder /app/public ./public

# Prepare .next directory with correct ownership
RUN mkdir .next && chown nextjs:nodejs .next

# Copy standalone build output and static bundle files
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Create pristine template for runtime route rewrites
RUN cp .next/routes-manifest.json .next/routes-manifest.template.json && \
    chown nextjs:nodejs .next/routes-manifest.template.json

# Run as unprivileged non-root user
USER nextjs

EXPOSE 3000

# Container healthcheck using Alpine busybox wget
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Start Next.js standalone Node.js production server
CMD ["node", "server.js"]
