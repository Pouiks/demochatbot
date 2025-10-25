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

# Exposer le port
EXPOSE 5173

# Commande pour lancer l'application en mode développement
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
