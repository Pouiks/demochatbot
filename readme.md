# 🏠 ECLA AI Search - Agent Commercial Intelligent

**Sarah**, votre conseillère en logement IA qui remplace vos commerciaux.

---

## 🚀 Démarrage Ultra-Rapide

### 1. Prérequis
- ✅ Docker Desktop installé et lancé
- ✅ Clé API OpenAI (GPT-4)

### 2. Configuration

Créez `backend/.env` :
```bash
OPENAI_API_KEY=sk-votre-cle-ici
```

### 3. Lancement (1 clic ou 1 commande !)

**Windows - Double-clic** :
```
📂 START_ECLA.bat  ← Double-cliquez !
```

**Windows - PowerShell** :
```powershell
.\start.ps1
```

**Linux/Mac** :
```bash
./start.sh
```

### 4. Accès

🌐 **Application** : http://localhost:5173  
⚙️ **Administration** : http://localhost:5173 (bouton ⚙️ en haut à droite)  
🔧 **API Recherche** : http://localhost:8000/docs  
🔧 **API Admin** : http://localhost:8001/docs  
📊 **Qdrant** : http://localhost:6333/dashboard

---

## 💡 Ce qui est automatisé

Le script fait **tout automatiquement** :

1. ✅ Vérifie Docker
2. ✅ **Tue les processus Python en cours**
3. ✅ **Supprime l'ancien conteneur Qdrant**
4. ✅ Arrête les conteneurs Docker Compose
5. ✅ Build les images
6. ✅ Lance les 4 services (Qdrant, Backend, Admin, Frontend)
7. ✅ Vérifie que tout fonctionne
8. ✅ Affiche les logs

**Plus de conflits de ports !** 🎉

---

## ⚙️ Nouvelle fonctionnalité : Interface d'administration

### Gérez votre contenu en temps réel !

L'interface d'administration vous permet de :

#### 📚 **Documentation**
- ✅ Ajouter/modifier/supprimer des informations sur vos services
- ✅ Gérer la FAQ, les partenariats, les procédures
- ✅ Ré-indexation **automatique** dans Qdrant

#### 🏢 **Appartements**
- ✅ Ajouter des logements manuellement
- ✅ Importer un fichier JSON complet
- ✅ Supprimer des appartements
- ✅ Ré-indexation **automatique** dans Qdrant

**👉 Guide complet : [GUIDE_ADMIN.md](GUIDE_ADMIN.md)**

---

## 🤖 Discutez avec Sarah

Sarah est une **vraie conseillère commerciale IA** :

- ✅ Comprend le langage naturel
- ✅ Se souvient de la conversation
- ✅ Propose des alternatives intelligentes
- ✅ Guide vers la réservation
- ✅ **Jamais de mention de concurrents**

### Exemples de questions

```
"je cherche un logement pas cher"
→ Sarah propose Noisy-le-Grand à 590€

"appartement à Massy-Palaiseau"
→ Sarah affiche 4 logements avec cards

"studio proche de Genève"
→ Sarah propose Archamps avec navette

"c'est quoi les services chez ECLA ?"
→ Sarah répond puis propose de chercher un logement
```

---

## 📊 Résidences disponibles

| Ville | Logements | Prix |
|-------|-----------|------|
| **Massy-Palaiseau** | 4 | 650€ - 950€ |
| **Noisy-le-Grand** | 4 | 590€ - 920€ |
| **Villejuif** | 4 | 630€ - 930€ |
| **Archamps (Genève)** | 5 | 720€ - 1100€ |

**Total : 17 logements** (Studios + T2)

---

## 🛠️ Fichiers utiles (1 clic)

| Fichier | Action |
|---------|--------|
| **START_ECLA.bat** | 🚀 Démarrer tout le projet |
| **STOP_ECLA.bat** | 🛑 Arrêter tous les services |
| **LOGS_ECLA.bat** | 📊 Voir les logs en direct |

## 🛠️ Commandes utiles (ligne de commande)

```bash
# Voir les logs
docker compose logs -f

# Arrêter tout
docker compose down

# Redémarrer un service
docker compose restart backend
```

---

## 📚 Documentation complète

- 📖 [QUICKSTART.md](QUICKSTART.md) - Guide de démarrage détaillé
- 📖 [README_PROJET.md](README_PROJET.md) - Architecture et roadmap
- ⚙️ [GUIDE_ADMIN.md](GUIDE_ADMIN.md) - **NOUVEAU** : Guide d'administration complètement

---

## 🎯 Tech Stack

- **Backend** : FastAPI, OpenAI GPT-4, Qdrant
- **Frontend** : React, TypeScript, Vite
- **Infrastructure** : Docker, Docker Compose

---

**Créé avec ❤️ pour révolutionner la recherche de logement étudiant**
