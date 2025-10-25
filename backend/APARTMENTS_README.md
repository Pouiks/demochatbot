# 🏠 Intégration des Appartements dans le Chatbot

## ✅ Ce qui a été fait

### 1. **Ingestion des données**
- ✅ 100 appartements chargés depuis `apartments_descriptions_fr.jsonl`
- ✅ Génération d'embeddings OpenAI pour chaque appartement
- ✅ Indexation dans Qdrant (collection `chunks`)
- ✅ Métadonnées enrichies : ville, prix, surface, équipements, etc.

### 2. **Amélioration du système**
- ✅ Prompt optimisé pour la recherche d'appartements
- ✅ Détection automatique des requêtes liées aux logements
- ✅ Réponses structurées avec prix, caractéristiques et comparaisons

### 3. **Fichiers créés/modifiés**
- `ingest_apartments.py` : Script d'ingestion des appartements
- `search_server.py` : Prompt amélioré pour gérer les appartements
- `apartments_descriptions_fr.jsonl` : Données sources (100 appartements)

---

## 🎯 Utilisation

### Exemples de questions que le chatbot peut gérer :

**Recherches simples :**
- "Je cherche un T1 à Lyon"
- "Studio à Paris"
- "Appartement à Bordeaux"

**Recherches avec budget :**
- "Appartement meublé à Paris de moins de 800€"
- "T1 pas cher à Lille"
- "Studio autour de 300€ à Marseille"

**Recherches avec critères :**
- "T2 avec balcon à Toulouse"
- "Appartement meublé avec parking à Nantes"
- "Studio avec ascenseur à Nice"

**Recherches par disponibilité :**
- "Appartement disponible immédiatement"
- "T1 disponible en octobre 2025"

---

## 📊 Statistiques des données

- **Total appartements** : 100
- **Villes couvertes** : Paris, Lyon, Marseille, Toulouse, Bordeaux, Nantes, Nice, Lille, Rennes, Montpellier
- **Types** : T1 (studios) et T2 (2 pièces)
- **Prix** : De 226€ à 1518€ CC par mois
- **Caractéristiques** : Meublé/non meublé, parking, balcon, ascenseur, internet

---

## 🔄 Ajouter plus d'appartements

Pour ajouter de nouveaux appartements :

```bash
# 1. Ajouter les appartements au fichier apartments_descriptions_fr.jsonl
# Format JSONL : une ligne = un appartement JSON

# 2. Relancer l'ingestion
cd backend
python ingest_apartments.py
```

---

## 🧪 Tester le système

### 1. Vérifier les données dans Qdrant
```bash
curl http://localhost:6333/collections/chunks
```

### 2. Tester une recherche via l'API
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Je cherche un T1 à Lyon\", \"summarize\": true}"
```

### 3. Utiliser le frontend
Ouvrir http://localhost:5173 et poser des questions !

---

## 💡 Comment ça marche ?

1. **Recherche sémantique** : La question de l'utilisateur est convertie en embedding
2. **Similarité vectorielle** : Qdrant trouve les 5 appartements/infos les plus pertinents
3. **Prompt intelligent** : Le système détecte si ce sont des appartements ou des infos générales
4. **Réponse GPT-4** : Génère une réponse conversationnelle avec tous les détails

---

## 🎨 Format des données sources

Chaque ligne du fichier JSONL contient :

```json
{
  "id": "unique-id",
  "text": "Description textuelle enrichie de l'appartement",
  "metadata": {
    "city": "Lyon",
    "postal_code": "69001",
    "rooms": 1,
    "surface_m2": 26.4,
    "furnished": true,
    "rent_cc_eur": 550.66,
    "availability_date": "2025-09-20",
    "energy_label": "D",
    "residence_name": "...",
    "synthesized": true
  }
}
```

---

## 🚀 Prochaines étapes possibles

- [ ] Ajouter des photos des appartements
- [ ] Intégrer un système de réservation
- [ ] Ajouter des filtres avancés (DPE, étage, etc.)
- [ ] Créer des alertes pour les nouveaux appartements
- [ ] Statistiques et recommandations personnalisées

---

**Date de mise à jour** : 24 octobre 2025  
**Statut** : ✅ Opérationnel

