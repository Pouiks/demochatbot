import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from openai import OpenAI
from dotenv import load_dotenv
import hashlib

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

qdrant = QdrantClient(host=os.getenv("QDRANT_HOST", "localhost"), port=int(os.getenv("QDRANT_PORT", "6333")))

COLLECTION_NAME = "chunks"

# Crée la collection si elle n'existe pas
if COLLECTION_NAME not in [c.name for c in qdrant.get_collections().collections]:
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

def generate_id(text):
    return int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (10 ** 12)

def embed(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# Charge les chunks
with open("ecla_chunks_classified.jsonl", "r", encoding="utf-8") as f:
    lines = [json.loads(line) for line in f]

points = []

for i, chunk in enumerate(lines):
    try:
        if not isinstance(chunk, dict):
            print(f"⚠️ Ligne {i+1} ignorée: format invalide")
            continue
            
        if "content" not in chunk:
            print(f"⚠️ Ligne {i+1} ignorée: pas de champ 'content'")
            continue
            
        if "metadata" not in chunk:
            print(f"⚠️ Ligne {i+1} ignorée: pas de champ 'metadata'")
            continue
            
        content = chunk["content"]
        metadata = chunk["metadata"]
        vector = embed(content)
        point = PointStruct(
            id=generate_id(content),
            vector=vector,
            payload={
                "content": content,
                **metadata
            }
        )
        points.append(point)
    except Exception as e:
        print(f"⚠️ Erreur ligne {i+1}: {e}")
        continue

# Envoi dans Qdrant
qdrant.upsert(
    collection_name=COLLECTION_NAME,
    points=points
)

print(f"Ingeste {len(points)} chunks dans Qdrant")
