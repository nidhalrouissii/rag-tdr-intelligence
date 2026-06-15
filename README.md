# 🤖 RAG TdR Intelligence

> Système de recherche intelligente de Termes de Référence (TdR) basé sur une architecture **Agentic RAG** industrialisable.

---

## 📋 Description

**TdR Intelligence** est une application web permettant l'enrichissement et l'optimisation des requêtes de recherche relatives aux missions et aux profils/compétences demandés, sur la base du contenu structuré de 100 Termes de Référence (TdR).

L'application permet de :
- Lancer des recherches sémantiques sur une base de 100 TdR
- Filtrer par domaine, pays, région, bailleur
- Visualiser les résultats avec scores de pertinence
- Afficher les profils et compétences exigés
- Voir les missions similaires

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                     │
│                  Interface EY-inspired                   │
└─────────────────────┬───────────────────────────────────┘
                      │ /api/agent | /api/rechercher
┌─────────────────────▼───────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Agentic RAG Pipeline                │    │
│  │                                                  │    │
│  │  Query → Retrieval → Self-Reflection → LLM       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │ Qdrant       │    │ Groq (llama-3.3-70b)         │   │
│  │ Vector Store │    │ Génération de réponses        │   │
│  └──────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Pipeline d'ingestion

Le pipeline est composé de 6 phases :

| Phase | Fichier | Description |
|-------|---------|-------------|
| 1 | `phase1_extract.py` | Extraction du texte (natif + OCR Tesseract) |
| 2 | `phase2_clean.py` | Nettoyage du texte (emails, URLs, bruit OCR) |
| 3 | `phase3_chunking.py` | Découpage en chunks de 400 caractères |
| 4 | `phase4_embedding.py` | Génération des embeddings (multilingual-e5-base) |
| 5 | `phase5_index.py` | Indexation dans Qdrant (768 dimensions, COSINE) |
| 6 | `phase6_metadata.py` | Extraction des métadonnées via LLM (Mistral/Ollama) |

---

## 🧠 Décisions Techniques

### Modèle d'embedding
- **Choix** : `intfloat/multilingual-e5-base` (768 dimensions)
- **Raison** : Supporte français, anglais et arabe. Conçu spécifiquement pour le retrieval avec préfixes `query:` / `passage:`, contrairement à `paraphrase-multilingual-MiniLM` qui est optimisé pour la similarité sémantique générale.

### Chunking
- **chunk_size** : 400 caractères
- **chunk_overlap** : 80 caractères
- **Raison** : Les TdR contiennent des passages courts et structurés. Un chunk_size de 2000 noyait les informations clés et réduisait la précision du retrieval.

### Vector Store
- **Choix** : Qdrant
- **Raison** : Performance élevée, filtrage par payload (pays, domaine, bailleur), déploiement Docker simple.

### LLM de génération
- **Choix** : Groq API (llama-3.3-70b-versatile)
- **Raison** : Inférence ultra-rapide, gratuit pour des volumes modérés, excellente qualité multilingue.

### Architecture Agentic RAG
- **Self-Reflection** : Le système évalue automatiquement la pertinence des chunks récupérés via le score moyen cosinus.
- **Retry** : Si le score moyen < 0.60, le système relance une recherche plus large (top_k=10).
- **Anti-hallucination** : Le prompt interdit explicitement au LLM de créer des informations absentes du contexte.

---

## 🚀 Installation et Exécution

### Prérequis
- Docker Desktop
- Git
- Compte Groq (API Key gratuite sur https://console.groq.com)
- Compte HuggingFace (token sur https://huggingface.co/settings/tokens)

### 1. Cloner le repository
```bash
git clone https://github.com/nidhalrouissii/rag-tdr-intelligence.git
cd rag-tdr-intelligence
```

### 2. Configurer les variables d'environnement
Créez un fichier `.env` à la racine :
```env
GROQ_API_KEY=votre_groq_api_key
HF_TOKEN=votre_huggingface_token
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### 3. Ajouter les TdR
Placez vos fichiers PDF dans `data/tdr/`

### 4. Lancer les conteneurs
```bash
docker compose up -d
```

### 5. Lancer le pipeline d'ingestion
```bash
# Extraction et nettoyage (à faire une seule fois)
docker exec -it backend python backend/ingestion/phase1_extract.py
docker exec -it backend python backend/ingestion/phase2_clean.py
docker exec -it backend python backend/ingestion/phase3_chunking.py
docker exec -it backend python backend/ingestion/phase4_embedding.py
docker exec -it backend python backend/ingestion/phase6_metadata.py

# Indexation dans Qdrant
docker exec -it -e QDRANT_HOST=qdrant backend python backend/indexing/phase5_index.py
```

### 6. Accéder à l'application
```
http://localhost
```

### API Swagger
```
http://localhost:8000/docs
```

---

## 📁 Structure du projet

```
RAG/
├── backend/
│   ├── agent/
│   │   └── phase7_retrieval.py
        └── phase10_agentic_rag.py
│   ├── api/
│   │   └── phase9_api.py             # API FastAPI
│   ├── indexing/
│   │   └── phase5_index.py           # Indexation Qdrant
│   └── ingestion/
│       ├── phase1_extract.py         # Extraction PDF
│       ├── phase2_clean.py           # Nettoyage texte
│       ├── phase3_chunking.py        # Chunking
│       ├── phase4_embedding.py       # Embeddings
│       └── phase6_metadata.py        # Métadonnées LLM
├── frontend/
│   └── src/
│       └── App.jsx                   # Interface React
├── data/
│   ├── tdr/                          # PDFs sources (non versionné)
│   ├── phase1_extracted.json
│   ├── phase2_cleaned.json
│   ├── phase3_chunks.json
│   └── phase6_metadata.json
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── requirements.txt
└── README.md
```

---

## 🐳 Services Docker

| Service | Port | Description |
|---------|------|-------------|
| frontend | 80 | Interface React (Nginx) |
| backend | 8000 | API FastAPI |
| qdrant | 6333 | Vector Store |
| ollama | 11434 | LLM local (optionnel) |

---

## 📊 Performances

- **Score moyen de pertinence** : 0.88+ sur les requêtes testées
- **Modèle embedding** : multilingual-e5-base (768 dim)
- **Chunks indexés** : 2906 chunks issus de 47 TdR validés
- **Temps de réponse** : ~3-5 secondes par requête

---

## 👤 Auteur

**Nidhal Rouissi**  
GitHub : [@nidhalrouissii](https://github.com/nidhalrouissii)
