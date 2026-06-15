import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

INPUT_FILE = "data/phase4_embeddings.json"
METADATA_FILE = "data/phase6_metadata.json"
COLLECTION_NAME = "tdr_collection"

# Connexion à Qdrant
print("🔄 Connexion à Qdrant...")
import os
client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)
print("✅ Connecté !\n")

# Charger les chunks avec embeddings
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)
print(f"📄 {len(chunks)} chunks à indexer...\n")

# Charger les métadonnées et indexer par filename
with open(METADATA_FILE, "r", encoding="utf-8") as f:
    metadata_list = json.load(f)
metadata_index = {m["filename"]: m for m in metadata_list}
print(f"🏷️  {len(metadata_index)} métadonnées chargées\n")

# Supprimer la collection si elle existe déjà
collections = [c.name for c in client.get_collections().collections]
if COLLECTION_NAME in collections:
    client.delete_collection(COLLECTION_NAME)
    print(f"🗑️  Ancienne collection supprimée")

# Créer la collection (384 dimensions = paraphrase-multilingual-MiniLM-L12-v2)
client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=768,
        distance=Distance.COSINE
    )
)
print(f"✅ Collection '{COLLECTION_NAME}' créée\n")

# Indexer par batch de 100
BATCH_SIZE = 100
total_indexe = 0

for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i+BATCH_SIZE]
    
    points = []
    for chunk in batch:
        meta = metadata_index.get(chunk["filename"], {})
        
        points.append(PointStruct(
            id=chunk["chunk_id"],
            vector=chunk["embedding"],
            payload={
                # Infos chunk
                "doc_id":             chunk["doc_id"],
                "filename":           chunk["filename"],
                "methode_extraction": chunk["methode_extraction"],
                "chunk_index":        chunk["chunk_index"],
                "total_chunks":       chunk["total_chunks"],
                "texte":              chunk["texte"],
                "nb_caracteres":      chunk["nb_caracteres"],
                # Métadonnées enrichies
                "titre": meta.get("titre", ""),
                "domaine": (meta.get("domaine") or "").lower(),
                "bailleur": (meta.get("bailleur") or "").lower(),
                "pays":     (meta.get("pays") or "").lower(),
                "region": meta.get("region", ""),
                "langue": meta.get("langue", ""),
                "duree_mission": meta.get("duree_mission", ""),
                "experience_annees": meta.get("experience_annees", ""), 
                "competences": meta.get("competences", []),
                "profils_requis": meta.get("profils_requis", []),
                "description": meta.get("description", "")
            }
        ))
    
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    total_indexe += len(batch)
    print(f"✅ Indexé {total_indexe}/{len(chunks)} chunks")

# Vérification finale
info = client.get_collection(COLLECTION_NAME)
print(f"\n{'='*50}")
print(f"✅ Indexation terminée !")
print(f"📊 Chunks indexés     : {info.points_count}")
print(f"📐 Dimensions         : 384")
print(f"📏 Distance           : COSINE")
print(f"🏷️  Métadonnées        : pays, domaine, bailleur, région, langue, compétences")
print("=" * 50)