"""
Script de démarrage pour le serveur d'administration
Attend que Qdrant soit prêt avant de démarrer
"""

import os
import time
from qdrant_client import QdrantClient

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

def wait_for_qdrant(max_attempts=30):
    """Attendre que Qdrant soit prêt"""
    print("⏳ Attente de Qdrant (Admin)...")
    
    for attempt in range(max_attempts):
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            # Tester la connexion
            client.get_collections()
            print("✅ Qdrant est prêt ! (Admin)")
            return True
        except Exception as e:
            print(f"⏳ Tentative {attempt + 1}/{max_attempts}... ({e})")
            time.sleep(2)
    
    raise Exception("❌ Impossible de se connecter à Qdrant après 60 secondes")

def main():
    print("=" * 50)
    print("🔧 Démarrage du serveur d'administration")
    print("=" * 50)
    
    # Attendre que Qdrant soit prêt
    wait_for_qdrant()
    
    print("🚀 Démarrage du serveur admin...\n")
    
    # Démarrer Uvicorn
    os.execvp("uvicorn", ["uvicorn", "admin_server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"])

if __name__ == "__main__":
    main()

