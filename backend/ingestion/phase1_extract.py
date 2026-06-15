import fitz  # pymupdf
import pytesseract
from PIL import Image
import io
import os
import json
import requests

# ============================================================
# CONFIG
# ============================================================

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

PDF_FOLDER = "data/tdr"
OUTPUT_FILE = "data/phase1_extracted.json"

OLLAMA_URL = "http://localhost:11434/api/generate"


# ============================================================
# ⚡ QUICK FILTER (FAST + SAFE)
# ============================================================
def quick_filter(text):
    keywords = [
        "tdr", "terms of reference", "consultant",
        "mission", "objectives", "livrables",
        "scope", "duration", "deliverables"
    ]
    text_lower = text.lower()
    score = sum(k in text_lower for k in keywords)
    return score >= 2


# ============================================================
# 🧠 LLM FILTER (STRICT + SAFE)
# ============================================================
def is_tdr(text):
    prompt = f"""
You are a document classifier.

Task: Decide if this document is a "Terms of Reference (ToR / TdR)".

Return ONLY:
YES or NO

TdR usually contains:
- objectives
- mission description
- tasks
- deliverables
- consultant profile

NOT TdR:
- reports
- slides
- catalogs
- manuals
- scientific papers

Text:
{text[:1500]}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0}
            },
            timeout=60
        )

        data = response.json()
        result = data.get("response", "").strip().upper()

        if result.startswith("YES"):
            return True
        if result.startswith("NO"):
            return False

        # SAFE DEFAULT = reject (important pour éviter bruit)
        return False

    except Exception as e:
        print(f"⚠️ LLM error: {e}")
        return False


# ============================================================
# 📄 PDF TYPE DETECTION
# ============================================================
def is_scanned_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return len(text.strip()) < 100


# ============================================================
# 📄 NATIVE EXTRACTION
# ============================================================
def extract_native(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


# ============================================================
# 🖼 OCR EXTRACTION
# ============================================================
def extract_ocr(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        text += pytesseract.image_to_string(
            img,
            lang="fra+eng+ara",
            config="--psm 3"
        ) + "\n"

    doc.close()
    return text


# ============================================================
# 🚀 PIPELINE
# ============================================================

fichiers = sorted(os.listdir(PDF_FOLDER))

resultats = []
erreurs = []

natifs = 0
scanned = 0
skipped = 0

print(f"📄 Traitement de {len(fichiers)} fichiers...\n")

for i, fichier in enumerate(fichiers):

    if not fichier.lower().endswith(".pdf"):
        continue

    chemin = os.path.join(PDF_FOLDER, fichier)

    try:
        # 1. extraction
        if is_scanned_pdf(chemin):
            texte = extract_ocr(chemin)
            scanned += 1
        else:
            texte = extract_native(chemin)
            natifs += 1

        # 2. quick filter
        if not quick_filter(texte):
            print(f"❌ Skip (quick): {fichier}")
            skipped += 1
            continue

        # 3. LLM filter
        if not is_tdr(texte):
            print(f"❌ Skip (LLM): {fichier}")
            skipped += 1
            continue

        # 4. save
        resultats.append({
            "id": i,
            "filename": fichier,
            "nb_caracteres": len(texte),
            "texte": texte[:50000]
        })

        print(f"✅ TdR accepté : {fichier}")

    except Exception as e:
        print(f"⚠️ Erreur : {fichier} → {e}")
        erreurs.append(fichier)


# ============================================================
# 💾 SAVE
# ============================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)

print("\n==============================")
print(f"✅ Natifs   : {natifs}")
print(f"🔍 Scannés  : {scanned}")
print(f"❌ Skip     : {skipped}")
print(f"⚠️ Errors   : {len(erreurs)}")
print(f"📁 Output   : {OUTPUT_FILE}")
print("==============================")