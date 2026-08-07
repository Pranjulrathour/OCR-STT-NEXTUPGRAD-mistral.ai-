FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# npm ci demands byte-exact lockfile consistency, but this tree has
# platform-gated optional native binaries (Tailwind's Oxide engine,
# ESLint's resolver bindings) that make npm hoist the tree differently
# per OS -- a lockfile written on Windows can fail npm ci's strict check
# on Linux even though it's fully valid. npm install still resolves
# from the lockfile's pinned versions but tolerates that platform drift.
RUN npm install --no-audit --no-fund

FROM node:22-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=build /app/public ./public
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

USER appuser
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "fetch('http://localhost:3000').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["npm", "start"]
