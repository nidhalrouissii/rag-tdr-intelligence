from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# ==============================
# IMPORT AGENT (SAFE PATH)
# ==============================
import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

from backend.agent.phase10_agentic_rag import agentic_rag


# ============================================================
# CONFIG
# ============================================================

COLLECTION_NAME = "tdr_collection"
SCORE_MIN = 0.25

app = FastAPI(
    title="RAG TdR API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# QDRANT CLIENT
# ============================================================

client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)

# ============================================================
# EMBEDDING MODEL (LAZY)
# ============================================================

model = None

def get_model():
    global model
    if model is None:
        print("🔄 Loading embedding model...")
        model = SentenceTransformer("intfloat/multilingual-e5-base")
        print("✅ Model loaded")
    return model


# ============================================================
# PYDANTIC MODELS
# ============================================================

class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    filtre_pays: Optional[str] = None
    filtre_domaine: Optional[str] = None
    filtre_bailleur: Optional[str] = None
    filtre_region: Optional[str] = None


class ChunkResult(BaseModel):
    score: float
    titre: str
    pays: Optional[str]
    bailleur: Optional[str]
    domaine: Optional[str]
    region: Optional[str] = None
    texte: str
    profils_requis: Optional[List[str]] = []
    competences: Optional[List[str]] = []


class AgentResponse(BaseModel):
    question: str
    reponse: str
    sources: List[ChunkResult]
    nb_chunks: int
    reflexion: dict


# ============================================================
# RETRIEVAL SIMPLE
# ============================================================

def rechercher(question, top_k, filtre_pays, filtre_domaine, filtre_bailleur, filtre_region=None):

    vector = get_model().encode("query: " + question, normalize_embeddings=True).tolist()

    conditions = []

    if filtre_pays:
        conditions.append(FieldCondition(key="pays", match=MatchValue(value=filtre_pays.lower())))
    if filtre_domaine:
        conditions.append(FieldCondition(key="domaine", match=MatchValue(value=filtre_domaine.lower())))
    if filtre_bailleur:
        conditions.append(FieldCondition(key="bailleur", match=MatchValue(value=filtre_bailleur.lower())))
    if filtre_region:
        conditions.append(FieldCondition(key="region", match=MatchValue(value=filtre_region.lower())))

    filtre_qdrant = Filter(must=conditions) if conditions else None

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=top_k,
        query_filter=filtre_qdrant,
        with_payload=True
    )

    chunks = []

    for r in response.points:

        score = getattr(r, "score", 0)

        if score < SCORE_MIN:
            continue

        p = r.payload

        chunks.append({
            "score": round(score, 4),
            "texte": p.get("texte", ""),
            "titre": p.get("titre") or p.get("filename", ""),
            "pays": p.get("pays", ""),
            "bailleur": p.get("bailleur", ""),
            "domaine": p.get("domaine", ""),
            "region": p.get("region", ""),
            "profils_requis": p.get("profils_requis", []),
            "competences": p.get("competences", [])
        })

    return chunks


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {"message": "Agentic RAG TdR API", "status": "ok"}


@app.get("/health")
def health():
    try:
        info = client.get_collection(COLLECTION_NAME)
        return {
            "status": "ok",
            "qdrant": "connected",
            "chunks": info.points_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent", response_model=AgentResponse)
def endpoint_agent(req: QuestionRequest):

    print("🔥 QUESTION:", req.question)

    try:
        resultat = agentic_rag(
            req.question,
            req.top_k,
            req.filtre_pays,
            req.filtre_domaine,
            req.filtre_bailleur
        )
        return AgentResponse(**resultat)

    except Exception as e:
        import traceback
        print("\n❌ ERROR FULL TRACEBACK:\n")
        traceback.print_exc()

        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/rechercher")
def endpoint_rechercher(req: QuestionRequest):
    try:
        chunks = rechercher(
            req.question,
            req.top_k,
            req.filtre_pays,
            req.filtre_domaine,
            req.filtre_bailleur,
            req.filtre_region
        )
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.phase9_api:app", host="0.0.0.0", port=8000, reload=True)