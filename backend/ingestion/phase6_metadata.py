import json
import requests
import time

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/phase2_cleaned.json"
OUTPUT_FILE = "data/phase6_metadata.json"

OLLAMA_URL = "http://localhost:11434/api/generate"

# ============================================================
# PROMPT STRUCTURÉ
# ============================================================

PROMPT_TEMPLATE = """
Tu es un expert en appels d'offres et marchés publics internationaux.

Réponds UNIQUEMENT avec un objet JSON valide.

Aucun commentaire.
Aucune explication.
Aucun markdown.
Aucun texte avant ou après le JSON.

Si une information est absente, mets null.

IMPORTANT :
Le champ "pays" doit contenir un pays.

Exemples corrects :
- Tunisie
- Maroc
- Mauritanie
- Sénégal

Exemples interdits :
- Tunisien
- Marocain
- Mauritanien
- Sénégalais

Format attendu :

{
  "titre": "titre de la mission",
  "domaine": "Santé, Education, Infrastructure, Agriculture, Environnement, Finance, Juridique, Communication, Technologie, Autre",
  "bailleur": "ex: Banque Mondiale, Union Européenne, AFD, PNUD, UNICEF",
  "pays": "pays concerné",
  "region": "région",
  "date_debut": null,
  "date_fin": null,
  "date_limite_candidature": null,
  "duree_mission": "ex: 6 mois",
  "profils_requis": [],
  "competences": [],
  "experience_annees": "ex: 5 ans",
  "langue": "français / anglais / arabe",
  "budget": null,
  "description": "résumé en 2 phrases maximum"
}

Document :

{texte}
"""

# ============================================================
# SAFE PARSING
# ============================================================

def safe_json_load(text):
    """Nettoie et parse JSON depuis le LLM"""

    text = text.strip()

    # retirer markdown éventuel
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]

    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    text = text.strip()

    try:
        return json.loads(text)

    except Exception:
        print("⚠️ JSON invalide détecté :")
        print(text[:500])
        return None


# ============================================================
# APPEL OLLAMA AVEC RETRY
# ============================================================

def extraire_metadata(texte):

    prompt = PROMPT_TEMPLATE.replace(
        "{texte}",
        texte[:3000]
    )

    for attempt in range(3):

        try:

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0,
                        "num_predict": 800
                    }
                },
                timeout=180
            )

            if response.status_code != 200:
                raise Exception(
                    f"HTTP {response.status_code}"
                )

            data = response.json()

            if "response" not in data:
                raise Exception(
                    f"Réponse invalide : {data}"
                )

            metadata = safe_json_load(
                data["response"]
            )

            if metadata is not None:
                return metadata

            raise Exception("JSON invalide")

        except Exception as e:

            print(
                f"⚠️ Tentative {attempt+1}/3 échouée : {e}"
            )

            time.sleep(2)

    return None


# ============================================================
# CHARGEMENT DES DOCUMENTS
# ============================================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    documents = json.load(f)

print(f"📄 {len(documents)} documents à analyser...\n")

resultats = []
erreurs = []

# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

for i, doc in enumerate(documents):

    print(
        f"[{i+1}/{len(documents)}] "
        f"{doc['filename']}"
    )

    try:

        metadata = extraire_metadata(
            doc["texte"]
        )

        if metadata is None:
            raise Exception(
                "Aucune métadonnée récupérée"
            )

        resultat = {
            "id": doc["id"],
            "filename": doc["filename"],
            "methode_extraction": doc.get(
                "methode",
                "natif"
            ),

            "titre": metadata.get("titre"),
            "domaine": metadata.get("domaine"),
            "bailleur": metadata.get("bailleur"),
            "pays": metadata.get("pays"),
            "region": metadata.get("region"),
            "date_debut": metadata.get("date_debut"),
            "date_fin": metadata.get("date_fin"),
            "date_limite_candidature": metadata.get("date_limite_candidature"),
            "duree_mission": metadata.get("duree_mission"),
            "profils_requis": metadata.get("profils_requis", []),
            "competences": metadata.get("competences", []),
            "experience_annees": metadata.get("experience_annees"),
            "langue": metadata.get("langue"),
            "budget": metadata.get("budget"),
            "description": metadata.get("description")
        }

        resultats.append(resultat)

        print(
            f"   ✅ {metadata.get('titre', 'N/A')[:60]}"
        )
        print(
            f"   🌍 {metadata.get('pays', 'Unknown')}"
        )
        print(
            f"   🏦 {metadata.get('bailleur', 'Unknown')}"
        )

    except Exception as e:

        print(f"   ❌ erreur : {e}")

        erreurs.append(doc["filename"])

        # ====================================================
        # FALLBACK POUR ÉVITER DE CASSER QDRANT
        # ====================================================

        resultats.append({

            "id": doc["id"],
            "filename": doc["filename"],
            "methode_extraction": doc.get(
                "methode",
                "natif"
            ),

            "titre": doc["filename"],
            "domaine": "Autre",

            "bailleur": "Unknown",
            "pays": "Unknown",
            "region": "Unknown",

            "date_debut": None,
            "date_fin": None,
            "date_limite_candidature": None,

            "duree_mission": None,

            "profils_requis": [],
            "competences": [],

            "experience_annees": None,
            "langue": None,
            "budget": None,

            "description": None
        })

# ============================================================
# SAUVEGARDE
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        resultats,
        f,
        ensure_ascii=False,
        indent=2
    )

# ============================================================
# STATS FINALES
# ============================================================

print("\n" + "=" * 50)

print(
    f"✅ succès   : "
    f"{len(resultats) - len(erreurs)}"
)

print(
    f"⚠️ erreurs  : "
    f"{len(erreurs)}"
)

print(
    f"📁 fichier  : "
    f"{OUTPUT_FILE}"
)

print("=" * 50)