import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI
from dotenv import load_dotenv
import hashlib

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

qdrant = QdrantClient(host=os.getenv("QDRANT_HOST", "localhost"), port=int(os.getenv("QDRANT_PORT", "6333")))

COLLECTION_NAME = "chunks"

def generate_id(text):
    return int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (10 ** 12)

def embed(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# Charger les chunks d'appartements depuis le fichier téléchargé
print("[INFO] Chargement des appartements depuis apartments_descriptions_fr.jsonl...")
apartments_file = "apartments_descriptions_fr.jsonl"

with open(apartments_file, "r", encoding="utf-8") as f:
    lines = [json.loads(line) for line in f if line.strip()]

print(f"[OK] {len(lines)} appartements charges")
print(f"\n[INFO] Generation des embeddings et preparation pour Qdrant...")

points = []

for i, apt in enumerate(lines, 1):
    # Le texte descriptif est déjà dans le champ "text"
    content = apt["text"]
    metadata = apt["metadata"]
    
    # Afficher la progression
    city = metadata.get('city', 'N/A')
    rooms = metadata.get('rooms', 'N/A')
    rent = metadata.get('rent_cc_eur', 'N/A')
    
    print(f"  [{i}/{len(lines)}] {city} - {rooms} piece(s) - {rent} EUR/mois")
    
    # Générer l'embedding
    vector = embed(content)
    
    # Créer le point pour Qdrant avec toutes les métadonnées enrichies
    point = PointStruct(
        id=generate_id(content + apt['id']),
        vector=vector,
        payload={
            "content": content,
            "type": "appartement",  # Important pour filtrer par type
            "apartment_id": apt['id'],
            "url": f"mailto:contact@uxco-management.com?subject=Appartement {apt['id']}",
            "lang": "fr",
            **metadata  # Ajoute toutes les métadonnées (city, rooms, rent_cc_eur, etc.)
        }
    )
    points.append(point)

# Envoi dans Qdrant par batch
print(f"\n[INFO] Envoi vers Qdrant (collection: {COLLECTION_NAME})...")
batch_size = 100
for i in range(0, len(points), batch_size):
    batch = points[i:i+batch_size]
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=batch
    )
    print(f"   [OK] Batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1} envoye ({len(batch)} appartements)")

print(f"\n[SUCCESS] Ingestion terminee avec succes !")
print(f"[INFO] {len(points)} appartements indexes dans Qdrant")
print(f"\n[INFO] Le chatbot peut maintenant repondre aux questions sur les appartements !")
print(f"\n[EXEMPLES] Questions a poser :")
print(f"   - Je cherche un T1 a Lyon")
print(f"   - Appartement meuble a Paris de moins de 800 EUR")
print(f"   - Studio disponible immediatement a Bordeaux")
print(f"   - T2 avec balcon a Toulouse")

