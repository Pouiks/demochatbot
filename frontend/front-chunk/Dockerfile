# Multi-stage build pour optimiser la taille
FROM node:20-alpine AS builder

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm ci

# Copier le code source
COPY . .

# Build l'application
RUN npm run build

# Stage de production
FROM node:20-alpine

WORKDIR /app

# Copier uniquement les dépendances de production
COPY package*.json ./
RUN npm ci --only=production

# Copier le serveur Express
COPY server.js ./

# Copier les fichiers buildés depuis le stage builder
COPY --from=builder /app/dist ./dist

# Railway injecte dynamiquement $PORT (par défaut 3000)
ENV PORT=3000

# Exposer le port
EXPOSE 3000

# Démarrer le serveur Express
CMD ["node", "server.js"]

