# 🔄 Migration vers l'Admin Complet - Guide Rapide

## ✅ Ce qui a été modifié

### Backend
1. ✅ **`requirements.txt`** : Ajout de PyPDF2, python-docx, chardet
2. ✅ **`text_extractor.py`** : Nouveau module d'extraction de texte (PDF/DOCX/TXT)
3. ✅ **`admin_server.py`** : Ajout de 3 nouveaux endpoints
   - `POST /admin/documents/upload` : Upload de fichiers
   - `GET /admin/documents/search` : Recherche documents
   - `GET /admin/apartments/search` : Filtrage appartements

### Frontend
1. ✅ **`AdminPanelEnhanced.tsx`** : Nouveau composant complet (remplace `AdminPanel.tsx`)
2. ✅ **`AdminPanel.css`** : Ajout de styles pour modales, drag & drop, filtres
3. ✅ **`App.tsx`** : Import du nouveau composant

---

## 🚀 Comment Tester

### Étape 1 : Rebuild Docker (nécessaire pour les nouvelles dépendances Python)

#### Windows
```bash
# Arrêter et supprimer les containers
docker compose down

# Rebuild avec les nouvelles dépendances
docker compose build --no-cache

# Relancer
START_ECLA.bat
```

#### Mac/Linux
```bash
docker compose down
docker compose build --no-cache
./start.sh
```

**Important** : Le `--no-cache` force Docker à réinstaller les dépendances Python.

---

### Étape 2 : Accéder à l'Interface Admin

1. Ouvrez http://localhost:5173
2. Cliquez sur le bouton **⚙️** en haut à droite
3. Vous devriez voir la nouvelle interface avec :
   - Zone de drag & drop
   - Barre de recherche
   - Filtres pour appartements
   - Boutons d'édition partout

---

### Étape 3 : Tester l'Upload de Fichier

#### Test avec un PDF

1. Créez un fichier `test.pdf` avec du texte (ou utilisez un PDF existant)
2. Dans l'onglet **📚 Documentation** :
   - Glissez-déposez le PDF dans la zone
   - OU cliquez pour parcourir et sélectionner
3. Observez :
   - ⏳ "Upload en cours..."
   - ✅ Message de succès : "Fichier 'test.pdf' uploadé. X chunks créés..."
   - Les nouveaux documents apparaissent dans la liste

#### Test avec un DOCX

1. Créez un fichier `services.docx` dans Word avec plusieurs paragraphes
2. Uploadez-le de la même manière
3. Vérifiez que les chunks sont créés

#### Test avec un TXT

1. Créez un `faq.txt` avec du contenu
2. Uploadez-le
3. Vérifiez l'extraction

---

### Étape 4 : Tester la Recherche de Documents

1. Dans la barre de recherche (en haut à droite de la liste) :
   - Tapez "service" → Seuls les docs avec "service" s'affichent
   - Tapez "ecla" → Filtrage en temps réel
2. Effacez → Tous les documents réapparaissent

---

### Étape 5 : Tester l'Édition de Document

1. Cliquez sur **✏️ Modifier** sur n'importe quel document
2. Une modale s'ouvre
3. Modifiez le contenu
4. Cliquez **✅ Sauvegarder**
5. Observez :
   - Message de succès
   - La liste se recharge
   - Le changement est visible

---

### Étape 6 : Tester les Filtres d'Appartements

1. Allez dans l'onglet **🏢 Appartements**
2. Testez les filtres :
   - **Ville** : Tapez "massy" → Seuls les appartements de Massy s'affichent
   - **Prix min** : Entrez "400" → Seuls les >400€ s'affichent
   - **Prix max** : Entrez "600" → Seuls les <600€ s'affichent
   - **Type** : Sélectionnez "Studio (T1)" → Seuls les T1 s'affichent
3. Combinez les filtres : Massy + 400-600€ + T1

---

### Étape 7 : Tester l'Ajout Manuel d'Appartement

1. Remplissez le formulaire :
   - Ville : Villejuif
   - Type : T2
   - Loyer : 720€
   - Surface : 40m²
   - Meublé : Oui
   - Date : 2025-01-01
2. Cliquez **✅ Ajouter**
3. Vérifiez :
   - Message de succès
   - Nouvel appartement dans la liste
   - Fichier `apartments_ecla_real.jsonl` mis à jour

---

### Étape 8 : Tester l'Édition d'Appartement

1. Cliquez **✏️ Modifier** sur un appartement
2. Changez le loyer (ex: 450€ → 480€)
3. Cliquez **✅ Sauvegarder**
4. Vérifiez que le changement est persisté

---

### Étape 9 : Vérifier la Persistance

1. Arrêtez le projet : `docker compose down`
2. Relancez : `START_ECLA.bat` (ou `./start.sh`)
3. Allez dans l'admin
4. Vérifiez que :
   - ✅ Tous vos documents uploadés sont toujours là
   - ✅ Tous vos appartements modifiés ont les bonnes valeurs
   - ✅ Le chat peut répondre avec les nouveaux contenus

---

### Étape 10 : Tester le Chat avec les Nouvelles Données

1. Retournez au chat (bouton **💬 Retour au chat**)
2. Posez une question sur le contenu d'un PDF que vous avez uploadé
3. Vérifiez que l'IA répond correctement
4. Cherchez un appartement que vous avez modifié
5. Vérifiez que les infos (prix, ville, etc.) sont à jour dans les cards

---

## 🐛 Dépannage

### Problème : "Form data requires python-multipart"
**Solution** : Rebuild Docker avec `docker compose build --no-cache`

### Problème : Upload ne fonctionne pas
**Cause** : Les nouvelles dépendances ne sont pas installées
**Solution** :
```bash
docker compose down
docker compose build --no-cache backend
docker compose build --no-cache admin
docker compose up -d
```

### Problème : "Module not found: text_extractor"
**Cause** : Le fichier n'est pas monté dans le container
**Solution** : Vérifiez que `./backend:/app` est bien dans les volumes de docker-compose.yml

### Problème : Les modifications ne persistent pas
**Cause** : Volume Qdrant supprimé
**Solution** : Ne jamais utiliser `docker compose down -v`

---

## 📊 Vérification Manuelle des Fichiers

Si vous voulez vérifier que les données sont bien sauvegardées :

### Documents
```bash
# Ouvrir le fichier JSONL
notepad backend/ecla_chunks_classified.jsonl
```
Cherchez vos nouveaux documents (ID contient le nom du fichier uploadé)

### Appartements
```bash
# Ouvrir le fichier JSONL
notepad backend/apartments_ecla_real.jsonl
```
Vérifiez que vos modifications sont là

---

## ✅ Checklist de Validation

- [ ] Drag & drop de PDF fonctionne
- [ ] Upload de DOCX crée des chunks
- [ ] Upload de TXT détecte l'encodage
- [ ] Recherche de documents filtre en temps réel
- [ ] Édition de document ouvre une modale
- [ ] Sauvegarde de document fonctionne
- [ ] Suppression de document avec confirmation
- [ ] Ajout manuel d'appartement fonctionne
- [ ] Filtres d'appartements fonctionnent (ville, prix, type)
- [ ] Édition d'appartement ouvre une modale
- [ ] Sauvegarde d'appartement met à jour le JSONL
- [ ] Suppression d'appartement fonctionne
- [ ] Upload JSON remplace tous les appartements
- [ ] Ré-indexation complète fonctionne
- [ ] Persistance après redémarrage Docker
- [ ] Le chat répond avec les nouvelles données

---

## 🎯 Cas d'Usage Réel

### Scénario : Ajouter une Politique de Remboursement

1. Créez un fichier Word `politique_remboursement.docx` :
   ```
   Politique de Remboursement ECLA
   
   Les remboursements sont possibles jusqu'à 30 jours avant la date d'arrivée.
   Au-delà, seuls 50% du montant sont remboursés.
   En cas de force majeure, remboursement intégral possible sur justificatif.
   ```

2. Uploadez dans l'admin (catégorie : Procédure)

3. Allez dans le chat et demandez : "Quelle est votre politique de remboursement ?"

4. L'IA devrait répondre en citant votre document !

---

**Vous êtes maintenant prêt à utiliser l'admin complet ! 🚀**

En cas de problème, consultez `ADMIN_COMPLET.md` pour les détails techniques.

