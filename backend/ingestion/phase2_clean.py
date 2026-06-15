import json
import re

INPUT_FILE = "data/phase1_extracted.json"
OUTPUT_FILE = "data/phase2_cleaned.json"


# ============================================================
# 🧹 CLEAN TEXT
# ============================================================
def clean_text(text):
    if not text:
        return ""

    # 1. caractères invisibles
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 2. emails
    text = re.sub(r'\S+@\S+', ' ', text)

    # 3. URLs
    text = re.sub(r'http\S+|www\.\S+', ' ', text)

    # 4. page numbers
    text = re.sub(r'\n\s*-?\s*\d+\s*-?\s*\n', '\n', text)
    text = re.sub(r'\bPage\s+\d+(\s*(of|sur|/)\s*\d+)?\b', '', text, flags=re.IGNORECASE)

    # 5. OCR noise (••••••, ----)
    text = re.sub(r'[•·▪■]{2,}', ' ', text)
    text = re.sub(r'[-_=*]{3,}', ' ', text)

    # 6. espaces
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


# ============================================================
# 📥 LOAD DATA
# ============================================================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    documents = json.load(f)

print(f"📄 Nettoyage de {len(documents)} documents...\n")

resultats = []

# ============================================================
# 🔄 PROCESS
# ============================================================
for doc in documents:

    try:
        texte_original = doc.get("texte", "")
        texte_nettoye = clean_text(texte_original)

        doc_nettoye = doc.copy()
        doc_nettoye["texte"] = texte_nettoye
        doc_nettoye["nb_caracteres_original"] = len(texte_original)
        doc_nettoye["nb_caracteres_nettoye"] = len(texte_nettoye)

        resultats.append(doc_nettoye)

        print(f"✅ {doc.get('filename','unknown')[:50]}")
        print(f"   {len(texte_original)} → {len(texte_nettoye)}")

    except Exception as e:
        print(f"⚠️ Erreur doc: {e}")


# ============================================================
# 💾 SAVE
# ============================================================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 50)
print(f"✅ Documents nettoyés : {len(resultats)}")
print(f"📁 Sauvegardé : {OUTPUT_FILE}")
print("=" * 50)