# ── Stage 1: Install dependencies ─────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json .
RUN npm install

# ── Stage 2: Serve the static site ────────────────────
FROM node:20-alpine

WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

EXPOSE 3000
CMD ["npx", "serve", ".", "-p", "3000"]
