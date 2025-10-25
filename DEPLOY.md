# 🚀 Déploiement sur Railway

## Prérequis
- Compte Railway (gratuit)
- Votre clé OpenAI

## Étapes de déploiement

### 1. Installer Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login et initialisation
```bash
railway login
railway init
```

### 3. Configurer les variables d'environnement
Dans le dashboard Railway, ajoutez :
```
OPENAI_API_KEY=sk-proj-votre-cle-openai-ici
QDRANT_HOST=localhost
QDRANT_PORT=6333
NODE_ENV=production
PYTHONUNBUFFERED=1
```

### 4. Déployer
```bash
railway up
```

## Services déployés
- **Backend FastAPI** : API de recherche sémantique
- **Qdrant** : Base de données vectorielle
- **Frontend React** : Interface utilisateur

## URLs après déploiement
- **API** : https://votre-app.railway.app/docs
- **Frontend** : https://votre-app.railway.app/

## Test local avec Docker
```bash
# Lancer tous les services
docker-compose up --build

# Accéder à l'application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000/docs
# Qdrant: http://localhost:6333/dashboard
```

## Ingestion des données
Les données seront automatiquement ingérées au premier démarrage via `init.sh`.

## 🎯 Votre démo sera accessible publiquement !
