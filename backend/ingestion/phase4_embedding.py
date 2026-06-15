import json
from sentence_transformers import SentenceTransformer

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/phase3_chunks.json"
OUTPUT_FILE = "data/phase4_embeddings.json"

# ============================================================
# CHARGEMENT MODELE EMBEDDING
# ============================================================

print("🔄 Chargement du modèle multilingue...")

# Français + Anglais + Arabe
model = SentenceTransformer("intfloat/multilingual-e5-base")

print("✅ Modèle chargé !\n")

# ============================================================
# CHARGEMENT CHUNKS
# ============================================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Supprimer les chunks vides
chunks = [c for c in chunks if c["texte"].strip()]

print(f"📄 {len(chunks)} chunks à embedder...\n")

# ============================================================
# EXTRACTION DES TEXTES
# ============================================================

textes = ["passage: " + chunk["texte"] for chunk in chunks]

# ============================================================
# GENERATION DES EMBEDDINGS
# ============================================================

print("🔄 Génération des embeddings...")

embeddings = model.encode(
    textes,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)

print("\n✅ Embeddings générés")
print(f"📐 Shape : {embeddings.shape}")
print(f"📏 Dimensions : {embeddings.shape[1]}")

# ============================================================
# AJOUT DES EMBEDDINGS AUX CHUNKS
# ============================================================

resultats = []

for i, chunk in enumerate(chunks):

    chunk_embedding = chunk.copy()

    chunk_embedding["embedding"] = embeddings[i].tolist()

    resultats.append(chunk_embedding)

# ============================================================
# SAUVEGARDE
# ============================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        resultats,
        f,
        ensure_ascii=False,
        indent=2
    )

# ============================================================
# STATISTIQUES
# ============================================================

print("\n" + "=" * 50)
print(f"✅ Chunks traités : {len(resultats)}")
print(f"📐 Dimension vecteur : {embeddings.shape[1]}")
print(f"📁 Sauvegardé : {OUTPUT_FILE}")
print("=" * 50)