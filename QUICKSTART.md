# 🚀 ECLA AI Search - Démarrage Rapide

## 📋 Prérequis

- **Docker Desktop** installé et lancé
  - Windows/Mac : [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
  - Linux : `sudo apt install docker.io docker-compose`
- **OpenAI API Key** (pour GPT-4 et embeddings)
  - Obtenez-la sur [platform.openai.com](https://platform.openai.com/api-keys)

---

## ⚡ Lancement en 1 commande

### Windows (PowerShell)

```powershell
.\start.ps1
```

### Linux / Mac

```bash
./start.sh
```

---

## 🎯 Configuration initiale

1. **Configurez votre clé OpenAI**
   
   Éditez `backend/.env` :
   ```env
   OPENAI_API_KEY=sk-votre-cle-ici
   ```

2. **Lancez le projet**
   
   Le script va automatiquement :
   - ✅ Vérifier Docker
   - ✅ Créer le fichier `.env` si absent
   - ✅ Arrêter les conteneurs existants
   - ✅ Construire les images Docker
   - ✅ Démarrer Qdrant (base vectorielle)
   - ✅ Démarrer le Backend (FastAPI)
   - ✅ Démarrer le Frontend (React)

3. **Accédez à l'application**
   
   🌐 **Frontend** : [http://localhost:5173](http://localhost:5173)
   
   📊 **Qdrant Dashboard** : [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
   
   🔧 **API Swagger** : [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Commandes utiles

### Voir les logs en direct
```bash
docker compose logs -f
```

### Voir les logs d'un service spécifique
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f qdrant
```

### Arrêter tous les services
```bash
docker compose down
```

### Redémarrer un service
```bash
docker compose restart backend
docker compose restart frontend
```

### Reconstruire et redémarrer
```bash
docker compose up -d --build
```

### Voir l'état des services
```bash
docker compose ps
```

---

## 📊 Ingérer les données

### 1. Données documentaires (ECLA infos)

```bash
docker compose exec backend python ingest_qdrant.py
```

### 2. Appartements (résidences ECLA)

```bash
docker compose exec backend python ingest_apartments.py
```

**Résultat attendu** : 17 appartements dans 4 villes (Massy-Palaiseau, Noisy-le-Grand, Villejuif, Archamps)

---

## 🤖 Utilisation de Sarah (Agent IA)

Sarah est votre conseillère en logement IA qui :
- ✅ Comprend le langage naturel
- ✅ Mémorise la conversation
- ✅ Propose des alternatives intelligentes
- ✅ Guide vers la réservation
- ✅ **Jamais** de mention de concurrents

### Exemples de questions

**Recherche budget limité** :
```
"je cherche un logement pas cher pour étudiant"
→ Sarah propose Noisy-le-Grand à 590€
```

**Recherche ville spécifique** :
```
"appartement à Massy-Palaiseau"
→ Sarah affiche 4 logements avec détails
```

**Budget impossible** :
```
"studio à Paris pour 300€"
→ Sarah propose alternatives (Noisy, Villejuif, Massy)
```

**Questions sur services** :
```
"c'est quoi les services chez ECLA ?"
→ Sarah répond puis propose de chercher un logement
```

**Frontalier Suisse** :
```
"appartement proche de Genève"
→ Sarah affiche Archamps avec navette
```

---

## 🐛 Dépannage

### Port déjà utilisé

```bash
# Trouver le processus qui utilise le port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Tuer le processus
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

### Qdrant ne démarre pas

```bash
# Supprimer le volume et redémarrer
docker compose down -v
docker compose up -d
```

### Backend ne se connecte pas à Qdrant

Vérifiez que `QDRANT_HOST=qdrant` dans `backend/.env` (pas `localhost` !)

### Frontend ne se connecte pas au Backend

En développement local, le frontend utilise `http://localhost:8000` automatiquement.

---

## 📂 Structure du projet

```
ecla-ai-search/
├── backend/                     # API FastAPI
│   ├── search_server.py         # Agent commercial IA
│   ├── ingest_qdrant.py         # Ingestion docs ECLA
│   ├── ingest_apartments.py     # Ingestion appartements
│   ├── apartments_descriptions_fr.jsonl  # 17 logements ECLA
│   └── ecla_chunks_classified.jsonl      # Docs ECLA
├── frontend/front-chunk/        # Interface React
│   └── src/components/
│       └── SemanticSearch.tsx   # Chat avec Sarah
├── docker-compose.yml           # Orchestration Docker
├── start.ps1                    # Lancement Windows
└── start.sh                     # Lancement Linux/Mac
```

---

## 🎨 Personnalisation

### Modifier le nom de l'agent

Dans `backend/search_server.py` :
```python
system_prompt = """Tu es Sarah, conseillère en logement chez ECLA..."""
```

Dans `frontend/front-chunk/src/components/SemanticSearch.tsx` :
```typescript
content: "Bonjour ! Je suis Sarah, votre conseillère..."
```

### Ajouter des appartements

Éditez `backend/apartments_descriptions_fr.jsonl` puis :
```bash
docker compose exec backend python ingest_apartments.py
```

### Modifier l'UI

Les styles sont dans `frontend/front-chunk/src/index.css`

---

## 📝 Notes

- **Mémoire conversationnelle** : Les 6 derniers messages sont conservés
- **Fallback intelligent** : Si 0 résultat → élargissement automatique (-30% budget, toutes villes)
- **Filtres natifs Qdrant** : Ville, pièces, meublé
- **Post-filtrage** : Budget min/max, surface min

---

## 🆘 Support

Pour toute question ou problème :
1. Vérifiez les logs : `docker compose logs -f`
2. Testez l'API manuellement : [http://localhost:8000/docs](http://localhost:8000/docs)
3. Vérifiez Qdrant : [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## ✨ Bon développement ! 🚀

