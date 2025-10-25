"""
Serveur d'administration pour gérer les documents et appartements
Permet l'ajout/modification/suppression avec ré-indexation automatique
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import uuid
from datetime import datetime
import subprocess

app = FastAPI(title="ECLA Admin API")

# CORS pour le frontend admin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === CHEMINS DES FICHIERS ===
DOCUMENTS_FILE = "ecla_chunks_classified.jsonl"
APARTMENTS_FILE = "apartments_ecla_real.jsonl"
COLORS_CONFIG_FILE = "chat_colors_config.json"

# === ÉTAT DE L'INDEXATION ===
indexing_status = {
    "in_progress": False,
    "last_update": None,
    "documents_count": 0,
    "apartments_count": 0,
    "last_action": None
}

# === MODÈLES PYDANTIC ===

class Document(BaseModel):
    content: str
    url: Optional[str] = ""
    category: str  # "service", "faq", "partnership", etc.

class DocumentUpdate(BaseModel):
    id: str
    content: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None

class Apartment(BaseModel):
    city: str
    rooms: int
    rent_cc_eur: float
    surface_m2: float
    furnished: bool
    availability_date: str
    energy_label: Optional[str] = "N/A"
    postal_code: Optional[str] = ""

class ApartmentUpdate(BaseModel):
    id: str
    city: Optional[str] = None
    rooms: Optional[int] = None
    rent_cc_eur: Optional[float] = None
    surface_m2: Optional[float] = None
    furnished: Optional[bool] = None
    availability_date: Optional[str] = None

class ChatColorsConfig(BaseModel):
    user_message_color: str = "#667eea"  # Couleur des messages utilisateur
    user_avatar_color: str = "#10b981"   # Couleur de l'avatar utilisateur
    ai_message_color: str = "#ffffff"    # Couleur des messages AI
    ai_avatar_color: str = "#667eea"     # Couleur de l'avatar AI
    theme_background: str = "#667eea"     # Couleur du thème principal
    theme_gradient: str = "#764ba2"      # Couleur du dégradé

# === FONCTIONS DE CONFIGURATION DES COULEURS ===

def load_colors_config():
    """Charger la configuration des couleurs"""
    if os.path.exists(COLORS_CONFIG_FILE):
        try:
            with open(COLORS_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement de la config couleurs: {e}")
    
    # Configuration par défaut
    default_config = {
        "user_message_color": "#667eea",
        "user_avatar_color": "#10b981",
        "ai_message_color": "#ffffff",
        "ai_avatar_color": "#667eea",
        "theme_background": "#667eea",
        "theme_gradient": "#764ba2"
    }
    save_colors_config(default_config)
    return default_config

def save_colors_config(config: dict):
    """Sauvegarder la configuration des couleurs"""
    try:
        with open(COLORS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la config couleurs: {e}")
        return False

# === FONCTIONS DE RÉ-INDEXATION ===

def reindex_documents():
    """Ré-indexer les documents en arrière-plan"""
    indexing_status["in_progress"] = True
    indexing_status["last_action"] = "Ré-indexation documents..."
    try:
        print("[REINDEX] Démarrage ré-indexation documents...")
        result = subprocess.run(
            ["python", "ingest_qdrant.py"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            indexing_status["last_update"] = datetime.now().isoformat()
            indexing_status["documents_count"] = count_documents()
            indexing_status["last_action"] = "Documents ré-indexés avec succès"
            print("[REINDEX] Documents ré-indexés avec succès")
        else:
            error_msg = result.stderr if result.stderr else "Erreur inconnue"
            indexing_status["last_action"] = f"Erreur: {error_msg}"
            print(f"[ERROR] Erreur lors de la ré-indexation: {error_msg}")
    except Exception as e:
        indexing_status["last_action"] = f"Erreur: {str(e)}"
        print(f"[ERROR] Exception lors de la ré-indexation: {str(e)}")
    finally:
        indexing_status["in_progress"] = False

def reindex_apartments():
    """Ré-indexer les appartements en arrière-plan"""
    indexing_status["in_progress"] = True
    indexing_status["last_action"] = "Ré-indexation appartements..."
    try:
        print("[REINDEX] Démarrage ré-indexation appartements...")
        result = subprocess.run(
            ["python", "ingest_apartments.py"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            indexing_status["last_update"] = datetime.now().isoformat()
            indexing_status["apartments_count"] = count_apartments()
            indexing_status["last_action"] = "Appartements ré-indexés avec succès"
            print("[REINDEX] Appartements ré-indexés avec succès")
        else:
            error_msg = result.stderr if result.stderr else "Erreur inconnue"
            indexing_status["last_action"] = f"Erreur: {error_msg}"
            print(f"[ERROR] Erreur lors de la ré-indexation: {error_msg}")
    except Exception as e:
        indexing_status["last_action"] = f"Erreur: {str(e)}"
        print(f"[ERROR] Exception lors de la ré-indexation: {str(e)}")
    finally:
        indexing_status["in_progress"] = False

def count_documents() -> int:
    """Compter le nombre de documents"""
    if not os.path.exists(DOCUMENTS_FILE):
        return 0
    with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def count_apartments() -> int:
    """Compter le nombre d'appartements"""
    if not os.path.exists(APARTMENTS_FILE):
        return 0
    with open(APARTMENTS_FILE, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

# === ENDPOINTS DE STATUT ===

@app.get("/")
def root():
    return {"message": "ECLA Admin API", "status": "running"}

@app.get("/admin/status")
def get_status():
    """Obtenir l'état de l'indexation et les statistiques"""
    return {
        **indexing_status,
        "documents_count": count_documents(),
        "apartments_count": count_apartments()
    }

# === ENDPOINTS DOCUMENTS ===

@app.get("/admin/documents")
def list_documents():
    """Lister tous les documents"""
    if not os.path.exists(DOCUMENTS_FILE):
        return []
    
    documents = []
    with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                documents.append(doc)
    
    return documents

@app.post("/admin/documents")
async def add_document(doc: Document, background_tasks: BackgroundTasks):
    """Ajouter un document et ré-indexer automatiquement"""
    
    # Validation
    if not doc.content or len(doc.content) < 10:
        raise HTTPException(400, "Le contenu doit contenir au moins 10 caractères")
    
    # Lire les documents existants
    documents = []
    if os.path.exists(DOCUMENTS_FILE):
        with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    documents.append(json.loads(line))
    
    # Créer le nouveau document
    new_doc = {
        "id": str(uuid.uuid4()),
        "content": doc.content,
        "url": doc.url or "",
        "type": doc.category,
        "timestamp": datetime.now().isoformat()
    }
    documents.append(new_doc)
    
    # Sauvegarder
    with open(DOCUMENTS_FILE, "w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")
    
    # Lancer la ré-indexation en arrière-plan
    background_tasks.add_task(reindex_documents)
    
    return {
        "success": True,
        "message": "Document ajouté. Ré-indexation en cours...",
        "document": new_doc
    }

@app.put("/admin/documents")
async def update_document(doc: DocumentUpdate, background_tasks: BackgroundTasks):
    """Modifier un document existant"""
    
    if not os.path.exists(DOCUMENTS_FILE):
        raise HTTPException(404, "Aucun document trouvé")
    
    # Lire les documents
    documents = []
    found = False
    with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                if d.get("id") == doc.id:
                    # Mettre à jour les champs fournis
                    if doc.content is not None:
                        d["content"] = doc.content
                    if doc.url is not None:
                        d["url"] = doc.url
                    if doc.category is not None:
                        d["type"] = doc.category
                    d["timestamp"] = datetime.now().isoformat()
                    found = True
                documents.append(d)
    
    if not found:
        raise HTTPException(404, f"Document {doc.id} non trouvé")
    
    # Sauvegarder
    with open(DOCUMENTS_FILE, "w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")
    
    # Ré-indexer
    background_tasks.add_task(reindex_documents)
    
    return {
        "success": True,
        "message": "Document modifié. Ré-indexation en cours..."
    }

@app.delete("/admin/documents/{doc_id}")
async def delete_document(doc_id: str, background_tasks: BackgroundTasks):
    """Supprimer un document"""
    
    if not os.path.exists(DOCUMENTS_FILE):
        raise HTTPException(404, "Aucun document trouvé")
    
    # Lire et filtrer
    documents = []
    found = False
    with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                if d.get("id") != doc_id:
                    documents.append(d)
                else:
                    found = True
    
    if not found:
        raise HTTPException(404, f"Document {doc_id} non trouvé")
    
    # Sauvegarder
    with open(DOCUMENTS_FILE, "w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")
    
    # Ré-indexer
    background_tasks.add_task(reindex_documents)
    
    return {
        "success": True,
        "message": "Document supprimé. Ré-indexation en cours..."
    }

# === ENDPOINTS APPARTEMENTS ===

@app.get("/admin/apartments")
def list_apartments():
    """Lister tous les appartements"""
    if not os.path.exists(APARTMENTS_FILE):
        return []
    
    apartments = []
    with open(APARTMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                apt = json.loads(line)
                apartments.append(apt)
    
    return apartments

@app.post("/admin/apartments")
async def add_apartment(apt: Apartment, background_tasks: BackgroundTasks):
    """Ajouter un appartement et ré-indexer automatiquement"""
    
    # Validation
    if apt.rent_cc_eur <= 0:
        raise HTTPException(400, "Le loyer doit être supérieur à 0")
    if apt.surface_m2 <= 0:
        raise HTTPException(400, "La surface doit être supérieure à 0")
    
    # Lire les appartements existants
    apartments = []
    if os.path.exists(APARTMENTS_FILE):
        with open(APARTMENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    apartments.append(json.loads(line))
    
    # Créer le nouvel appartement
    apt_id = f"{apt.city.upper().replace(' ', '_')}_T{apt.rooms}_{str(uuid.uuid4())[:8]}"
    new_apt = {
        "id": apt_id,
        "metadata": {
            "city": apt.city,
            "rooms": apt.rooms,
            "rent_cc_eur": apt.rent_cc_eur,
            "surface_m2": apt.surface_m2,
            "furnished": apt.furnished,
            "availability_date": apt.availability_date,
            "energy_label": apt.energy_label or "N/A",
            "postal_code": apt.postal_code or ""
        }
    }
    apartments.append(new_apt)
    
    # Sauvegarder
    with open(APARTMENTS_FILE, "w", encoding="utf-8") as f:
        for apartment in apartments:
            f.write(json.dumps(apartment, ensure_ascii=False) + "\n")
    
    # Ré-indexer
    background_tasks.add_task(reindex_apartments)
    
    return {
        "success": True,
        "message": "Appartement ajouté. Ré-indexation en cours...",
        "apartment": new_apt
    }

@app.put("/admin/apartments")
async def update_apartment(apt: ApartmentUpdate, background_tasks: BackgroundTasks):
    """Modifier un appartement existant"""
    
    if not os.path.exists(APARTMENTS_FILE):
        raise HTTPException(404, "Aucun appartement trouvé")
    
    # Lire les appartements
    apartments = []
    found = False
    with open(APARTMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                a = json.loads(line)
                if a.get("id") == apt.id:
                    # Mettre à jour les champs fournis
                    if apt.city is not None:
                        a["metadata"]["city"] = apt.city
                    if apt.rooms is not None:
                        a["metadata"]["rooms"] = apt.rooms
                    if apt.rent_cc_eur is not None:
                        a["metadata"]["rent_cc_eur"] = apt.rent_cc_eur
                    if apt.surface_m2 is not None:
                        a["metadata"]["surface_m2"] = apt.surface_m2
                    if apt.furnished is not None:
                        a["metadata"]["furnished"] = apt.furnished
                    if apt.availability_date is not None:
                        a["metadata"]["availability_date"] = apt.availability_date
                    if apt.energy_label is not None:
                        a["metadata"]["energy_label"] = apt.energy_label
                    if apt.postal_code is not None:
                        a["metadata"]["postal_code"] = apt.postal_code
                    found = True
                apartments.append(a)
    
    if not found:
        raise HTTPException(404, f"Appartement {apt.id} non trouvé")
    
    # Sauvegarder
    with open(APARTMENTS_FILE, "w", encoding="utf-8") as f:
        for apartment in apartments:
            f.write(json.dumps(apartment, ensure_ascii=False) + "\n")
    
    # Ré-indexer
    background_tasks.add_task(reindex_apartments)
    
    return {
        "success": True,
        "message": "Appartement modifié. Ré-indexation en cours..."
    }

@app.delete("/admin/apartments/{apt_id}")
async def delete_apartment(apt_id: str, background_tasks: BackgroundTasks):
    """Supprimer un appartement"""
    
    if not os.path.exists(APARTMENTS_FILE):
        raise HTTPException(404, "Aucun appartement trouvé")
    
    # Lire et filtrer
    apartments = []
    found = False
    with open(APARTMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                a = json.loads(line)
                if a.get("id") != apt_id:
                    apartments.append(a)
                else:
                    found = True
    
    if not found:
        raise HTTPException(404, f"Appartement {apt_id} non trouvé")
    
    # Sauvegarder
    with open(APARTMENTS_FILE, "w", encoding="utf-8") as f:
        for apartment in apartments:
            f.write(json.dumps(apartment, ensure_ascii=False) + "\n")
    
    # Ré-indexer
    background_tasks.add_task(reindex_apartments)
    
    return {
        "success": True,
        "message": "Appartement supprimé. Ré-indexation en cours..."
    }

@app.post("/admin/apartments/upload")
async def upload_apartments_json(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Remplacer le fichier JSON des appartements et ré-indexer automatiquement"""
    
    # Valider le fichier
    if not file.filename.endswith(('.json', '.jsonl')):
        raise HTTPException(400, "Le fichier doit être au format JSON ou JSONL")
    
    # Lire et valider le contenu
    content = await file.read()
    try:
        # Essayer de parser en JSON
        data = json.loads(content.decode('utf-8'))
        
        # Valider la structure
        if isinstance(data, list):
            apartments = data
        else:
            raise ValueError("Le JSON doit être un tableau d'appartements")
        
        # Valider chaque appartement
        for apt in apartments:
            required_fields = ["id", "metadata"]
            if not all(field in apt for field in required_fields):
                raise ValueError(f"Appartement invalide: {apt.get('id', 'unknown')}")
            
            # Valider les métadonnées
            required_meta = ["city", "rooms", "rent_cc_eur", "surface_m2", "furnished"]
            if not all(field in apt["metadata"] for field in required_meta):
                raise ValueError(f"Métadonnées invalides pour: {apt['id']}")
        
    except Exception as e:
        raise HTTPException(400, f"JSON invalide: {str(e)}")
    
    # Convertir en JSONL si nécessaire
    jsonl_lines = []
    for apt in apartments:
        jsonl_lines.append(json.dumps(apt, ensure_ascii=False))
    
    # Sauvegarder
    with open(APARTMENTS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(jsonl_lines) + "\n")
    
    # Lancer la ré-indexation en arrière-plan
    background_tasks.add_task(reindex_apartments)
    
    return {
        "success": True,
        "message": f"{len(apartments)} appartements importés. Ré-indexation en cours...",
        "count": len(apartments)
    }

@app.post("/admin/reindex-all")
async def reindex_all(background_tasks: BackgroundTasks):
    """Ré-indexer TOUT manuellement (bouton de secours)"""
    background_tasks.add_task(reindex_documents)
    background_tasks.add_task(reindex_apartments)
    
    return {
        "success": True,
        "message": "Ré-indexation complète lancée en arrière-plan"
    }

# === NOUVEAUX ENDPOINTS - FONCTIONNALITÉS AVANCÉES ===

@app.post("/admin/documents/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    category: str = "service",
    background_tasks: BackgroundTasks = None
):
    """
    Upload d'un fichier (PDF/DOCX/TXT) et extraction automatique du texte
    Le texte est découpé en chunks et indexé automatiquement
    """
    from text_extractor import extract_and_chunk_file
    
    # Valider le format
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(400, "Format non supporté. Acceptés: PDF, DOCX, TXT")
    
    try:
        # Lire le contenu du fichier
        file_content = await file.read()
        
        # Extraire et découper en chunks
        chunks = extract_and_chunk_file(file.filename, file_content, max_chunk_length=500)
        
        if not chunks:
            raise HTTPException(400, "Aucun texte exploitable dans le fichier")
        
        # Lire les documents existants
        documents = []
        if os.path.exists(DOCUMENTS_FILE):
            with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        documents.append(json.loads(line))
        
        # Ajouter chaque chunk comme un document
        added_docs = []
        for i, chunk in enumerate(chunks):
            new_doc = {
                "id": f"{file.filename}_{i}_{str(uuid.uuid4())[:8]}",
                "content": chunk,
                "url": f"upload://{file.filename}",
                "type": category,
                "timestamp": datetime.now().isoformat(),
                "source_file": file.filename,
                "chunk_index": i
            }
            documents.append(new_doc)
            added_docs.append(new_doc)
        
        # Sauvegarder
        with open(DOCUMENTS_FILE, "w", encoding="utf-8") as f:
            for document in documents:
                f.write(json.dumps(document, ensure_ascii=False) + "\n")
        
        # Ré-indexer
        background_tasks.add_task(reindex_documents)
        
        return {
            "success": True,
            "message": f"Fichier '{file.filename}' uploadé. {len(chunks)} chunks créés. Ré-indexation en cours...",
            "chunks_count": len(chunks),
            "documents": added_docs
        }
        
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Erreur lors du traitement du fichier: {str(e)}")

@app.get("/admin/documents/search")
async def search_documents(q: str = ""):
    """Rechercher dans les documents par contenu ou type"""
    if not os.path.exists(DOCUMENTS_FILE):
        return []
    
    documents = []
    with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                # Recherche insensible à la casse
                if not q or q.lower() in doc.get("content", "").lower() or q.lower() in doc.get("type", "").lower():
                    documents.append(doc)
    
    return documents

@app.get("/admin/apartments/search")
async def search_apartments(
    city: str = None,
    min_price: float = None,
    max_price: float = None,
    rooms: int = None
):
    """Filtrer les appartements par critères"""
    if not os.path.exists(APARTMENTS_FILE):
        return []
    
    apartments = []
    with open(APARTMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                apt = json.loads(line)
                metadata = apt.get("metadata", {})
                
                # Appliquer les filtres
                if city and metadata.get("city", "").lower() != city.lower():
                    continue
                if rooms and metadata.get("rooms") != rooms:
                    continue
                if min_price and metadata.get("rent_cc_eur", 0) < min_price:
                    continue
                if max_price and metadata.get("rent_cc_eur", float('inf')) > max_price:
                    continue
                
                apartments.append(apt)
    
    return apartments

# === ENDPOINTS DE CONFIGURATION DES COULEURS ===

@app.get("/admin/colors")
async def get_colors_config():
    """Récupérer la configuration actuelle des couleurs"""
    config = load_colors_config()
    return {
        "success": True,
        "config": config
    }

@app.post("/admin/colors")
async def update_colors_config(config: ChatColorsConfig):
    """Mettre à jour la configuration des couleurs"""
    try:
        # Valider les couleurs hexadécimales
        hex_colors = [
            config.user_message_color,
            config.user_avatar_color,
            config.ai_message_color,
            config.ai_avatar_color,
            config.theme_background,
            config.theme_gradient
        ]
        
        for color in hex_colors:
            if not color.startswith('#') or len(color) != 7:
                raise HTTPException(400, f"Couleur invalide: {color}. Format attendu: #RRGGBB")
            
            # Vérifier que c'est bien hexadécimal
            try:
                int(color[1:], 16)
            except ValueError:
                raise HTTPException(400, f"Couleur hexadécimale invalide: {color}")
        
        # Sauvegarder la configuration
        config_dict = config.dict()
        if save_colors_config(config_dict):
            return {
                "success": True,
                "message": "Configuration des couleurs mise à jour avec succès",
                "config": config_dict
            }
        else:
            raise HTTPException(500, "Erreur lors de la sauvegarde de la configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erreur lors de la mise à jour: {str(e)}")

@app.post("/admin/colors/reset")
async def reset_colors_config():
    """Réinitialiser la configuration des couleurs aux valeurs par défaut"""
    default_config = {
        "user_message_color": "#667eea",
        "user_avatar_color": "#10b981",
        "ai_message_color": "#ffffff",
        "ai_avatar_color": "#667eea",
        "theme_background": "#667eea",
        "theme_gradient": "#764ba2"
    }
    
    if save_colors_config(default_config):
        return {
            "success": True,
            "message": "Configuration des couleurs réinitialisée",
            "config": default_config
        }
    else:
        raise HTTPException(500, "Erreur lors de la réinitialisation")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

