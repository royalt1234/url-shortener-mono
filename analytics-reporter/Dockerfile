# ── Stage 1: Install dependencies ──────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json .
RUN npm install --omit=dev

# ── Stage 2: Runtime image ──────────────────────────────
FROM node:20-alpine

WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY index.js .

EXPOSE 4000
CMD ["node", "index.js"]
