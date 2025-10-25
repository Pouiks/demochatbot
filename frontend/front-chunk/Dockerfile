# Dockerfile pour le développement local
FROM node:20-alpine

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier le code source
COPY . .

# Exposer le port Vite
EXPOSE 5173

# Démarrer Vite en mode dev avec hot-reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

