from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(host='localhost', port=6333)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

q = 'expertise gestion projet care leaving réunification gatekeeping protection remplacement consultants'
v = model.encode(q, normalize_embeddings=True).tolist()

r = client.query_points(collection_name='tdr_collection', query=v, limit=10, with_payload=True)
for p in r.points:
    titre = p.payload.get('titre', '')[:60]
    print(f'{p.score:.4f} | {titre}')

# Chercher tous les chunks de ce TdR spécifique
r2 = client.scroll(
    collection_name='tdr_collection',
    scroll_filter={
        "must": [{"key": "titre", "match": {"value": "Assistance technique pour la mise en œuvre de pilotes et modélisation dans le domaine de la Protection de Remplacement"}}]
    },
    limit=20,
    with_payload=True
)
print(f"\nChunks du TdR spécifique : {len(r2[0])}")
for p in r2[0]:
    print(f"  chunk {p.payload.get('chunk_index')} | {p.payload.get('texte', '')[:100]}")