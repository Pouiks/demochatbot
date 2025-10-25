# Dockerfile pour le frontend React
FROM node:20-alpine

# Définir le répertoire de travail
WORKDIR /app

# Copier package.json et package-lock.json
COPY package*.json ./

# Installer les dépendances
RUN npm ci

# Copier le code source
COPY . .

# Build de l'application React
RUN npm run build

# Exposer le port (Railway définit $PORT dynamiquement)
EXPOSE 5173

# Lancer le serveur Express pour servir les fichiers statiques
CMD ["npm", "start"]
