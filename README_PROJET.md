# 🏠 ECLA AI Search - Agent Commercial IA

**Agent conversationnel intelligent pour remplacer vos commerciaux et accompagner vos utilisateurs dans leur recherche de logement.**

---

## 🎯 Vision du projet

### Le problème
Les utilisateurs abandonnent la recherche car :
- ❌ Trop de filtres manuels
- ❌ Navigation complexe
- ❌ Pas d'accompagnement personnalisé
- ❌ Perte de prospects quand critères non trouvés

### La solution : Sarah, Agent Commercial IA
✅ **Conversationnel** : Langage naturel  
✅ **Intelligent** : Comprend l'intention  
✅ **Proactif** : Pose des questions  
✅ **Mémoire** : Se souvient de la conversation  
✅ **Commercial** : Propose alternatives, jamais de concurrents  
✅ **Guidant** : Accompagne jusqu'à la réservation  

---

## ⚡ Démarrage rapide

### 1️⃣ Installation

```bash
# Cloner le projet
git clone <repo-url>
cd ecla-ai-search

# Configurer l'API OpenAI
echo "OPENAI_API_KEY=sk-votre-cle" > backend/.env
```

### 2️⃣ Lancement (1 commande !)

**Windows** :
```powershell
.\start.ps1
```

**Linux/Mac** :
```bash
./start.sh
```

### 3️⃣ Accès

🌐 **Application** : [http://localhost:5173](http://localhost:5173)  
🔧 **API** : [http://localhost:8000/docs](http://localhost:8000/docs)  
📊 **Qdrant** : [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

📖 **Documentation complète** : Voir [QUICKSTART.md](QUICKSTART.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              UTILISATEUR                         │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────▼─────────┐
        │  Frontend React  │  ← Chat avec Sarah
        │  (Port 5173)     │
        └────────┬─────────┘
                 │ HTTP REST
        ┌────────▼─────────┐
        │  Backend FastAPI │  ← Agent IA commercial
        │  (Port 8000)     │  ← GPT-4 + embeddings
        └────┬──────┬──────┘
             │      │
    OpenAI API     │
             │      │
        ┌────▼──────▼──────┐
        │  Qdrant Vector DB│  ← Recherche sémantique
        │  (Port 6333)     │  ← 17 appartements ECLA
        └──────────────────┘
```

---

## 🤖 Sarah : L'Agent Commercial IA

### Persona
- **Nom** : Sarah
- **Rôle** : Conseillère en logement ECLA
- **Spécialité** : Étudiants et jeunes actifs
- **Personnalité** : Chaleureuse, proactive, orientée solution

### Capacités

#### 1️⃣ Analyse d'intention (GPT-4)
```
User: "j'ai besoin de trouver un toit à moins de 500 euros à paris"

Sarah analyse :
{
  "is_apartment_search": true,
  "criteria": {
    "max_budget": 500,
    "city": "Paris"
  }
}
```

#### 2️⃣ Recherche sémantique (Qdrant)
- Embeddings OpenAI (text-embedding-3-small)
- Filtres natifs : ville, pièces, meublé
- Post-filtrage : budget, surface

#### 3️⃣ Stratégie commerciale
```
0 résultat Paris < 500€
  ↓
Fallback automatique
  ↓
Élargir : toutes villes + budget +30%
  ↓
Proposer alternatives
```

#### 4️⃣ Réponse contextuelle (GPT-4)
```
Sarah: "Je n'ai pas d'appartements à Paris dans ce budget. 
       Par contre, j'ai 8 studios à partir de 590€ à 
       Noisy-le-Grand (20 min de Paris en RER A). 
       
       Souhaitez-vous que je vous les montre ?"
```

#### 5️⃣ Mémoire conversationnelle
- Garde les 6 derniers messages
- Affine les réponses selon le contexte
- Pose des questions de relance

---

## 📊 Données

### Résidences ECLA (17 appartements)

| Ville | Appartements | Prix min | Prix max |
|-------|--------------|----------|----------|
| **Massy-Palaiseau** | 4 | 650€ | 950€ |
| **Noisy-le-Grand** | 4 | 590€ | 920€ |
| **Villejuif** | 4 | 630€ | 930€ |
| **Archamps (Genève)** | 5 | 720€ | 1100€ |

**Total : 17 logements** (Studios + T2)

### Services inclus
- ✅ Wifi fibre
- ✅ Salle de sport
- ✅ Espace coworking
- ✅ Laverie
- ✅ Charges comprises

---

## 🎨 Interface utilisateur

### Design compact (style Airbnb/Booking)
- Cards horizontales ultra-compactes
- Affichage progressif (effet typing + fade-in)
- Prix mis en avant
- Détails essentiels visibles
- Bouton "En savoir plus"

### Responsive
- ✅ Desktop
- ✅ Tablet
- ✅ Mobile

---

## 🔧 Technologies

### Backend
- **FastAPI** : API REST
- **OpenAI GPT-4** : Agent commercial + analyse intention
- **OpenAI Embeddings** : Recherche sémantique
- **Qdrant** : Base vectorielle
- **Pydantic** : Validation de données

### Frontend
- **React 18** : Interface utilisateur
- **TypeScript** : Typage strict
- **Vite** : Build tool
- **CSS moderne** : Animations, gradients

### Infrastructure
- **Docker Compose** : Orchestration
- **Uvicorn** : Serveur ASGI
- **CORS** : Communication frontend/backend

---

## 🚀 Roadmap

### ✅ Phase 1 : MVP (Terminé)
- [x] Agent GPT-4 avec mémoire
- [x] Recherche sémantique Qdrant
- [x] 4 résidences ECLA réelles
- [x] Interface chat moderne
- [x] Fallback intelligent
- [x] Lancement 1 commande

### 🔨 Phase 2 : Production (À venir)
- [ ] Authentification utilisateur
- [ ] Système de réservation
- [ ] Notifications email
- [ ] Analytics (tracking conversations)
- [ ] A/B testing prompts
- [ ] Multi-langue (EN, ES)

### 🎯 Phase 3 : Scale (Futur)
- [ ] Fine-tuning GPT sur historique
- [ ] Recommandations ML
- [ ] Intégration CRM
- [ ] Chatbot vocal
- [ ] Widget embeddable

---

## 📈 Métriques de succès

### KPIs commerciaux
- ⬆️ **Taux de conversion** : Recherche → Réservation
- ⬇️ **Taux d'abandon** : Utilisateurs perdus
- ⬆️ **Durée de session** : Engagement
- ⬆️ **Nombre de questions** : Interaction

### KPIs techniques
- ⚡ **Latence réponse** : < 2s
- 🎯 **Pertinence résultats** : > 90%
- 🔧 **Uptime** : > 99.5%
- 💰 **Coût OpenAI** : < 0.50€/conversation

---

## 🤝 Contribution

### Modifier le comportement de Sarah

**Prompt système** : `backend/search_server.py`
```python
system_prompt = """Tu es Sarah, conseillère en logement chez ECLA..."""
```

**Message d'accueil** : `frontend/front-chunk/src/components/SemanticSearch.tsx`
```typescript
content: "Bonjour ! Je suis Sarah, votre conseillère..."
```

### Ajouter des appartements

1. Éditez `backend/apartments_descriptions_fr.jsonl`
2. Ré-ingérez : `docker compose exec backend python ingest_apartments.py`

### Modifier l'UI

Styles : `frontend/front-chunk/src/index.css`

---

## 📝 Licence

Propriétaire ECLA - Tous droits réservés

---

## 📞 Contact

Pour toute question technique ou commerciale :
- 📧 Email : tech@ecla.com
- 🌐 Site : [ecla.com](https://ecla.com)

---

**Créé avec ❤️ pour révolutionner la recherche de logement étudiant**

