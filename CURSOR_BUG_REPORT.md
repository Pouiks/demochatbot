# 🐛 BUG CRITIQUE - Cursor Tools (search_replace, write) sur Windows

## 📋 Environnement
- **OS**: Windows 11 (10.0.26100)
- **Workspace**: `C:\chunks` 
- **Docker**: Actif avec volumes montés
- **Shell**: PowerShell

## 🚨 Description du problème

Les outils `search_replace` et `write` de Cursor **NE MODIFIENT PAS les fichiers sur le disque** dans un environnement Windows.

### Symptômes
1. L'outil retourne `"The file ... has been updated"`
2. Le diff affiché dans Cursor montre les modifications
3. **MAIS** le fichier sur le disque reste INCHANGÉ
4. Les commandes shell (ex: `python -m py_compile`) montrent que l'erreur persiste
5. Même après `docker compose down`, le fichier reste non modifié

### Impact
- **BLOQUANT** pour le développement
- Impossible de corriger les erreurs de syntaxe
- Les scripts PowerShell externes fonctionnent, mais pas les tools Cursor
- Nécessite des manipulations manuelles (git checkout + édition manuelle)

## 🔍 Étapes pour reproduire

```xml
<invoke name="search_replace">
<parameter name="file_path">backend/search_server.py</parameter>
<parameter name="old_string">else:
    # Mode Local
qdrant_host = os.getenv("QDRANT_HOST", "localhost")</parameter>
<parameter name="new_string">else:
    # Mode Local
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")</parameter>
</invoke>
```

**Résultat attendu**: Le fichier devrait avoir 4 espaces d'indentation  
**Résultat réel**: Le fichier reste inchangé sur le disque

## ✅ Workaround qui fonctionne

```powershell
# PowerShell DIRECT fonctionne
$content = Get-Content backend\search_server.py -Raw
$content = $content -replace "pattern", "replacement"
$content | Set-Content backend\search_server.py -NoNewline
```

## 💬 Logs Cursor

```
<function_results>
The file backend/search_server.py has been updated. Here's a relevant snippet of the edited file:
    38|else:
    39|    # Mode Local (développement)
    40|    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    [...]
</function_results>
```

Mais `python -m py_compile backend\search_server.py` retourne toujours:
```
Sorry: IndentationError: expected an indented block after 'else' statement on line 38 (search_server.py, line 40)
```

## 🎯 Solution demandée

1. **Investiguer** pourquoi les tools ne commitent pas les changements sur le disque sous Windows
2. **Ajouter un flag de vérification** pour confirmer que le fichier est bien modifié
3. **Documenter** les limitations connues de Windows + Docker

## 📎 Fichiers concernés

- `backend/search_server.py` (830 lignes)
- Testé avec `search_replace` (40+ tentatives)
- Testé avec `write` (réécriture complète du fichier)

## 🔗 Contexte

Projet Python/FastAPI avec Docker Compose, développé sous Windows.  
Les tools Cursor sont essentiels pour l'efficacité du développement.  
Ce bug bloque complètement l'utilisation de l'IA pour corriger les erreurs.

---

**Merci de prioriser ce bug, il impacte l'expérience utilisateur sur Windows !** 🙏

