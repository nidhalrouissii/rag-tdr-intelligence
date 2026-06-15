import json
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# ============================================================
# CONFIGURATION
# ============================================================

COLLECTION_NAME = "tdr_collection"
TOP_K_RETRIEVAL = 15   # on prend large pour rerank
TOP_K_FINAL = 5        # résultat final
SCORE_MIN = 0.2        # seuil raisonnable cross-encoder

print("🔄 Chargement modèles...")

# embedding model (semantic search)
embedding_model = SentenceTransformer("intfloat/multilingual-e5-base")

# reranker (cross-encoder)
reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Qdrant client
client = QdrantClient(host="localhost", port=6333)

print("✅ Modèles et Qdrant prêts !")


# ============================================================
# RECHERCHE VECTORIELLE
# ============================================================

def rechercher(question: str,
               top_k: int = TOP_K_FINAL,
               filtre_pays: str = None,
               filtre_domaine: str = None,
               filtre_bailleur: str = None):

    # --------------------------------------------------------
    # 1. EMBEDDING
    # --------------------------------------------------------
    query_vector = embedding_model.encode("query: " + question, normalize_embeddings=True).tolist()

    # --------------------------------------------------------
    # 2. FILTRES
    # --------------------------------------------------------
    conditions = []

    if filtre_pays:
        conditions.append(
            FieldCondition(key="pays", match=MatchValue(value=filtre_pays))
        )

    if filtre_domaine:
        conditions.append(
            FieldCondition(key="domaine", match=MatchValue(value=filtre_domaine))
        )

    if filtre_bailleur:
        conditions.append(
            FieldCondition(key="bailleur", match=MatchValue(value=filtre_bailleur))
        )

    qdrant_filter = Filter(must=conditions) if conditions else None

    # --------------------------------------------------------
    # 3. RETRIEVAL (QDRANT)
    # --------------------------------------------------------
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=TOP_K_RETRIEVAL,
        query_filter=qdrant_filter,
        with_payload=True
    )

    candidates = response.points

    if not candidates:
        return []

    # --------------------------------------------------------
    # 4. RERANK (CROSS-ENCODER)
    # --------------------------------------------------------
    pairs = [
        (question, p.payload.get("texte", ""))
        for p in candidates
    ]

    rerank_scores = reranker.predict(pairs)

    # --------------------------------------------------------
    # 5. FUSION PROPRE
    # --------------------------------------------------------
    reranked = []

    for point, score in zip(candidates, rerank_scores):

        if score < SCORE_MIN:
            continue

        p = point.payload

        reranked.append({
            "score": float(score),   # score reranker uniquement
            "titre": p.get("titre", ""),
            "texte": p.get("texte", "")[:300],
            "filename": p.get("filename", ""),
            "pays": p.get("pays", ""),
            "domaine": p.get("domaine", ""),
            "bailleur": p.get("bailleur", "")
        })

    # tri final
    reranked = sorted(reranked, key=lambda x: x["score"], reverse=True)

    return reranked[:top_k]


# ============================================================
# AFFICHAGE
# ============================================================

def afficher(resultats, question):

    print("\n" + "=" * 60)
    print(f"❓ Question : {question}")
    print(f"🔍 Résultats : {len(resultats)}")
    print("=" * 60)

    for i, r in enumerate(resultats, 1):
        print(f"\n[{i}] Score : {round(r['score'], 3)}")
        print(f"📄 Titre  : {r['titre'] or r['filename']}")
        print(f"🌍 Pays   : {r['pays']} | 📂 {r['domaine']}")
        print(f"🏦 Bailleur: {r['bailleur']}")
        print(f"📝 Texte  : {r['texte']}...")


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    questions = [
        "expert en santé publique Afrique",
        "formation renforcement capacités",
        "consultant gestion projet Maroc",
        "appel d'offres eau infrastructure Afrique"
    ]

    for q in questions:
        afficher(rechercher(q), q)