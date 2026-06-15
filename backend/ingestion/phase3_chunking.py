import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

INPUT_FILE = "data/phase2_cleaned.json"
OUTPUT_FILE = "data/phase3_chunks.json"

# ============================================================
# ⚙️ SPLITTER CONFIG
# ============================================================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,        # ← diviser par 5
    chunk_overlap=80,     # ← overlap 25% pour ne pas couper les listes
    separators=["\n\n", "\n", ". ", " ", ""],
)

# ============================================================
# 📥 LOAD DATA
# ============================================================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    documents = json.load(f)

print(f"📄 Chunking de {len(documents)} documents...\n")

tous_chunks = []
chunk_id = 0

# ============================================================
# 🔄 PROCESS
# ============================================================
for doc in documents:

    texte = doc.get("texte", "").strip()

    if not texte:
        print(f"⏭️ Ignoré (vide) : {doc.get('filename','unknown')}")
        continue

    chunks = splitter.split_text(texte)

    for i, chunk in enumerate(chunks):

        tous_chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc.get("id", -1),
            "filename": doc.get("filename", "unknown"),
            "methode_extraction": doc.get("methode", "unknown"),
            "chunk_index": i,
            "total_chunks": len(chunks),
            "texte": chunk,
            "nb_caracteres": len(chunk)
        })

        chunk_id += 1

    print(f"✅ {doc.get('filename','unknown')[:50]} → {len(chunks)} chunks")

# ============================================================
# 💾 SAVE
# ============================================================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(tous_chunks, f, ensure_ascii=False, indent=2)

# ============================================================
# 📊 STATS SAFE
# ============================================================
nb_docs = len(documents)
nb_chunks = len(tous_chunks)

avg = nb_chunks / nb_docs if nb_docs > 0 else 0

print("\n" + "=" * 50)
print(f"✅ Documents : {nb_docs}")
print(f"🧩 Chunks    : {nb_chunks}")
print(f"📊 Moyenne   : {avg:.2f} chunks/doc")
print(f"📁 Output    : {OUTPUT_FILE}")
print("=" * 50)