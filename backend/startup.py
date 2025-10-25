"""
Script de démarrage intelligent pour le backend
Vérifie si les données existent dans Qdrant et les ingère si nécessaire
"""

import os
import time
import subprocess
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

COLLECTION_NAME = "chunks"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

def wait_for_qdrant(max_attempts=60):
    """Attendre que Qdrant soit prêt"""
    print("Attente de Qdrant...")
    
    for attempt in range(max_attempts):
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=5)
            # Tester la connexion avec un timeout court
            client.get_collections()
            print("✅ Qdrant est prêt !")
            return client
        except Exception as e:
            if attempt < 10:
                # Premières tentatives : attendre 1 seconde
                print(f"⏳ Tentative {attempt + 1}/{max_attempts}...")
                time.sleep(1)
            else:
                # Tentatives suivantes : attendre 2 secondes
                print(f"⏳ Tentative {attempt + 1}/{max_attempts}... ({str(e)[:50]})")
                time.sleep(2)
    
    raise Exception("❌ Impossible de se connecter à Qdrant après 2 minutes")

def collection_exists(client):
    """Vérifier si la collection existe et contient des données"""
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        points_count = collection_info.points_count
        print(f"📊 Collection '{COLLECTION_NAME}' trouvée avec {points_count} points")
        return points_count > 0
    except UnexpectedResponse:
        print(f"❌ Collection '{COLLECTION_NAME}' n'existe pas")
        return False
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification: {e}")
        return False

def ingest_data():
    """Ingérer les données initiales"""
    print("\n📥 Ingestion des données initiales...")
    
    # Ingérer les documents
    print("\n1️⃣ Ingestion des documents...")
    try:
        result = subprocess.run(
            ["python", "ingest_qdrant.py"],
            capture_output=True,
            text=True,
            timeout=60  # Timeout de 60 secondes
        )
        
        if result.returncode == 0:
            print("✅ Documents ingérés avec succès")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print("⚠️ Erreur lors de l'ingestion des documents:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout lors de l'ingestion des documents")
    except Exception as e:
        print(f"⚠️ Erreur inattendue: {e}")
    
    # Ingérer les appartements
    print("\n2️⃣ Ingestion des appartements...")
    try:
        result = subprocess.run(
            ["python", "ingest_apartments.py"],
            capture_output=True,
            text=True,
            timeout=60  # Timeout de 60 secondes
        )
        
        if result.returncode == 0:
            print("✅ Appartements ingérés avec succès")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print("⚠️ Erreur lors de l'ingestion des appartements:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout lors de l'ingestion des appartements")
    except Exception as e:
        print(f"⚠️ Erreur inattendue: {e}")

def main():
    print("=" * 50)
    print("🚀 Démarrage du backend ECLA AI Search")
    print("=" * 50)
    
    # Attendre que Qdrant soit prêt
    client = wait_for_qdrant()
    
    # Vérifier si les données existent
    if collection_exists(client):
        print("\n✅ Les données sont déjà présentes dans Qdrant")
        print("🚀 Démarrage du serveur...")
    else:
        print("\n⚠️ Aucune donnée trouvée dans Qdrant")
        ingest_data()
        print("\n✅ Ingestion terminée !")
        print("🚀 Démarrage du serveur...\n")
    
    # Démarrer Uvicorn
    os.execvp("uvicorn", ["uvicorn", "search_server:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    main()

