FROM node:24-bookworm-slim AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# Cache dependencies separately from application source.
COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/package.json
RUN --mount=type=cache,target=/root/.npm npm ci --workspace frontend

COPY docs ./docs
COPY frontend ./frontend
RUN npm run build --workspace frontend

FROM node:24-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

COPY --from=build --chown=node:node /app/frontend/.next/standalone ./
COPY --from=build --chown=node:node /app/frontend/.next/static ./frontend/.next/static

USER node
EXPOSE 3000
CMD ["node", "frontend/server.js"]
