# Build context is the repository root (npm workspaces span apps/web, contracts, packages/shared).
FROM node:20-slim

WORKDIR /repo

COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY contracts/package.json contracts/package.json
COPY packages/shared/package.json packages/shared/package.json
RUN npm ci

COPY apps/web apps/web
COPY packages/shared packages/shared

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm --workspace apps/web run build

EXPOSE 3000
CMD ["sh", "-c", "cd apps/web && npx next start -H 0.0.0.0 -p 3000"]
