FROM node:24-bookworm-slim AS dependencies
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# Cache dependencies separately from application source.
COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/package.json
RUN --mount=type=cache,target=/root/.npm npm ci --workspace frontend

FROM dependencies AS build
COPY README.md ./README.md
COPY docs ./docs
COPY frontend ./frontend
RUN npm run build --workspace frontend

FROM dependencies AS development
COPY --chown=node:node README.md ./README.md
COPY --chown=node:node docs ./docs
COPY --chown=node:node frontend ./frontend
RUN chown node:node /app/frontend /app/docs
USER node
EXPOSE 3000
CMD ["npm", "exec", "--workspace", "frontend", "--", "next", "dev", "--hostname", "0.0.0.0"]

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
