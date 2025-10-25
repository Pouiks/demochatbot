# Dockerfile pour le backend FastAPI
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Invalider le cache pour forcer la copie des nouveaux fichiers
ARG CACHEBUST=2

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 8000

# Commande pour lancer l'application
CMD ["python", "startup.py"]
