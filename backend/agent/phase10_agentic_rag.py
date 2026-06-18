from dotenv import load_dotenv
load_dotenv()

import json
import os
from groq import Groq
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# ============================================================
# CONFIGURATION
# ============================================================

COLLECTION_NAME = "tdr_collection"

SCORE_MIN = 0.25   # ✅ stable (ni trop strict ni trop bas)
LLM_DECISION_THRESHOLD = 0.60

GROQ_MODEL = "llama-3.3-70b-versatile"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)

model = SentenceTransformer("intfloat/multilingual-e5-base")


# ============================================================
# LLM CALL
# ============================================================

def appeler_llm(prompt: str, temperature: float = 0, max_tokens: int = 500) -> str:
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


# ============================================================
# ÉTAPE 1 — QUERY (SIMPLE MAIS STABLE)
# ============================================================

def expand_query(question: str) -> list[str]:
    # version stable (pas de hallucination LLM ici)
    return [question]


# ============================================================
# ÉTAPE 2 — RETRIEVAL
# ============================================================

def retrieval_multi_query(
    questions: list[str],
    top_k: int = 5,
    filtre_pays: str = None,
    filtre_domaine: str = None,
    filtre_bailleur: str = None
) -> list[dict]:

    conditions = []

    if filtre_pays:
        conditions.append(FieldCondition(key="pays", match=MatchValue(value=filtre_pays.lower())))
    if filtre_domaine:
        conditions.append(FieldCondition(key="domaine", match=MatchValue(value=filtre_domaine.lower())))
    if filtre_bailleur:
        conditions.append(FieldCondition(key="bailleur", match=MatchValue(value=filtre_bailleur.lower())))

    filtre_qdrant = Filter(must=conditions) if conditions else None

    results = {}

    for q in questions:

        vector = model.encode(
        "query: " + q,      
        normalize_embeddings=True
        ).tolist()

        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=top_k * 3,
            query_filter=filtre_qdrant,
            with_payload=True
        )

        for r in response.points:

            if r.score < SCORE_MIN:
                continue

            pid = r.id
            p = r.payload

            if pid not in results or r.score > results[pid]["score"]:
                results[pid] = {
                    "score": round(r.score, 4),
                    "texte": p.get("texte", ""),
                    "titre": p.get("titre") or p.get("filename", ""),
                    "filename": p.get("filename", ""),
                    "pays": p.get("pays", ""),
                    "bailleur": p.get("bailleur", ""),
                    "domaine": p.get("domaine", "")
                }

    sorted_results = sorted(results.values(), key=lambda x: x["score"], reverse=True)

    print(f"📦 {len(sorted_results[:top_k])} chunks retenus")

    return sorted_results[:top_k]


# ============================================================
# ÉTAPE 3 — SELF REFLECTION (FIXÉE)
# ============================================================

def self_reflection(question: str, chunks: list[dict]) -> dict:

    if not chunks:
        return {
            "pertinent": False,
            "raison": "Aucun résultat",
            "score_moyen": 0
        }

    score_moyen = sum(c["score"] for c in chunks) / len(chunks)

    # ========================================================
    # 🔥 FIX IMPORTANT : logique PRIORITAIRE
    # ========================================================

    if score_moyen >= LLM_DECISION_THRESHOLD:
        return {
            "pertinent": True,
            "raison": "Score élevé → résultats pertinents",
            "score_moyen": round(score_moyen, 3)
        }

    # fallback LLM seulement si score faible
    titres = [c["titre"] for c in chunks[:3]]

    prompt = f"""
Tu es un expert en évaluation de recherche documentaire.

Question: {question}
Résultats: {titres}
Score moyen: {score_moyen:.2f}

Réponds uniquement en JSON:
{{
"pertinent": true/false,
"raison": "courte explication"
}}
"""

    try:
        out = appeler_llm(prompt)

        if "```json" in out:
            out = out.split("```json")[1].split("```")[0].strip()

        return {
            **json.loads(out),
            "score_moyen": round(score_moyen, 3)
        }

    except:
        return {
            "pertinent": score_moyen >= 0.5,
            "raison": "fallback score",
            "score_moyen": round(score_moyen, 3)
        }


# ============================================================
# ÉTAPE 4 — GÉNÉRATION (ANTI HALLUCINATION)
# ============================================================

def generer_reponse(question: str, chunks: list[dict]) -> str:

    if not chunks:
        return "Aucun document pertinent trouvé."

    contexte = ""

    for i, c in enumerate(chunks, 1):
        contexte += f"""
SOURCE {i}
Titre: {c['titre']}
Pays: {c['pays']}
Texte: {c['texte'][:800]}
"""

    prompt = f"""
Tu es un expert en appels d'offres.

RÈGLES STRICTES:
- utilise uniquement les sources ci-dessous
- ne crée aucune information
- si absent → dis "non trouvé"
- quand tu cites une source, utilise son titre exact entre parenthèses
  ex: (Evaluation VSF-B 2017-2021) au lieu de "source 1"

CONTEXTE:
{contexte}

QUESTION:
{question}

Réponse claire et structurée:
"""

    return appeler_llm(prompt, temperature=0.2, max_tokens=1500)


# ============================================================
# PIPELINE COMPLET
# ============================================================

def agentic_rag(
    question: str,
    top_k: int = 5,
    filtre_pays: str = None,
    filtre_domaine: str = None,
    filtre_bailleur: str = None
):

    print("\n" + "="*60)
    print(f"🤖 QUESTION: {question}")
    print("="*60)

    # -------------------------
    # 1 retrieval
    # -------------------------
    print("\n🔍 Retrieval...")
    chunks = retrieval_multi_query(
        [question], top_k,
        filtre_pays=filtre_pays,
        filtre_domaine=filtre_domaine,
        filtre_bailleur=filtre_bailleur
    )

    # -------------------------
    # 2 reflection
    # -------------------------
    print("\n🧠 Reflection...")
    reflexion = self_reflection(question, chunks)

    print("Pertinent:", reflexion["pertinent"])
    print("Score moyen:", reflexion["score_moyen"])
    print("Raison:", reflexion["raison"])

    # -------------------------
    # retry si mauvais
    # -------------------------
    if not reflexion["pertinent"]:
        print("\n🔄 Retry plus large...")
        chunks = retrieval_multi_query([question], top_k=10)
        reflexion = self_reflection(question, chunks)

    # -------------------------
    # 3 génération
    # -------------------------
    print("\n💬 Génération...")
    reponse = generer_reponse(question, chunks)

    return {
        "question": question,
        "reponse": reponse,
        "sources": chunks,
        "nb_chunks": len(chunks),
        "reflexion": reflexion
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = agentic_rag(
        "Quels profils sont recherchés pour une mission santé en Afrique ?",
        top_k=5
    )

    print("\n" + "="*60)
    print("💬 RÉPONSE FINALE:\n")
    print(result["reponse"])

    print("\n📚 SOURCES:")
    for s in result["sources"]:
        print(f"- {s['score']} | {s['titre']}")