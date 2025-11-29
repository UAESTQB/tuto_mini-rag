# Tutoriel Mini-RAG - CFTL JTIA 2025 Paris

Application Flask pour le tutoriel de construction d'un pipeline RAG (Retrieval-Augmented Generation) avec un assistant testeur ISTQB certifié.

## 🎯 Description

Cette application implémente un pipeline RAG complet permettant de :
- **Indexer** des documents (PDF, DOCX, TXT, MD) avec FAISS
- **Rechercher** dans les documents via similarité vectorielle
- **Générer** des réponses contextuelles avec un LLM
- **Assister** dans les activités de test selon les standards ISTQB

L'assistant IA se comporte comme un **testeur certifié ISTQB** capable d'assister dans :
- 📋 **Analyse des tests** : Identifier les conditions de test
- 🎯 **Conception des tests** : Créer des cas de test détaillés
- ⚙️ **Implémentation des tests** : Préparer scripts et environnement
- ▶️ **Exécution des tests** : Définir procédures et critères

## 🔧 Modes de fonctionnement

L'application supporte deux modes configurables via le fichier `.env` :

### Mode OpenAI (par défaut)
- Embeddings : OpenAI text-embedding-3-small
- LLM : OpenAI GPT (configurable : gpt-4o-mini, gpt-4o, etc.)
- Clé API fournie pour l'atelier

### Mode Local
- Embeddings : Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2)
- LLM : Ollama (llama3.2:3b ou autre modèle)
- Fonctionne 100% en local sans API externe

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip

### Étapes d'installation

1. **Activer votre environnement virtuel** (si ce n'est pas déjà fait) :

**Windows (cmd.exe) :**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell) :**
```powershell
venv\Scripts\Activate.ps1
```

**Linux/Mac :**
```bash
source venv/bin/activate
```

2. **Installer les dépendances :**
```cmd
pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` à la racine du projet :

```env
# Configuration Flask
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Clé API OpenAI (fournie pour l'atelier)
OPENAI_API_KEY=votre_clé_api

# Mode de fonctionnement : 'openai' ou 'local'
EMBEDDING_MODE=openai
LLM_MODE=openai

# Modèles
OLLAMA_MODEL=llama3.2:3b
OPENAI_MODEL=gpt-4o
```

### Installation du mode local (optionnel)

Pour utiliser le mode local, installer Ollama :
- **Windows/Mac** : https://ollama.com/download
- **Linux** : `curl -fsSL https://ollama.com/install.sh | sh`

Puis télécharger un modèle :
```bash
ollama pull llama3.2:3b
```

## ▶️ Lancement de l'application

```cmd
python app.py
```

ou

```cmd
flask run
```

L'application sera accessible sur : http://localhost:5000

## 📁 Structure du projet

```
tuto_mini-rag/
├── app.py                      # Application Flask principale
├── requirements.txt            # Dépendances Python
├── .env                        # Variables d'environnement (non versionné)
├── modules/                    # Modules RAG
│   ├── document_processor.py  # Extraction de texte
│   ├── chunker.py             # Découpage en chunks
│   ├── indexer.py             # Indexation FAISS
│   ├── local_embedder.py      # Embeddings locaux
│   └── local_llm.py           # LLM local (Ollama)
├── templates/                  # Templates HTML
│   ├── index.html             # Page d'accueil
│   ├── upload.html            # Upload de documents
│   ├── indexation.html        # Indexation FAISS
│   ├── search.html            # Recherche et chat
│   └── navigation.html        # Menu de navigation
├── static/                     # Fichiers statiques
│   ├── css/                   # Styles CSS
│   └── js/                    # Scripts JavaScript
├── uploads/                    # Documents uploadés
└── data/                       # Index FAISS et métadonnées
```

## 🎓 Utilisation

### Étape 1 : Upload de documents
- Accédez à la page "Upload"
- Glissez-déposez vos documents (PDF, DOCX, TXT, MD)
- Les formats supportés : PDF, Word, Texte, Markdown

### Étape 2 : Indexation
- Allez sur la page "Indexation"
- Configurez les paramètres (chunk size, overlap)
- Lancez l'indexation FAISS
- L'index vectoriel sera créé automatiquement

### Étape 3 : Recherche et génération
- Page "Utiliser" pour interroger vos documents
- Posez vos questions en langage naturel
- L'assistant testeur ISTQB répond en se basant sur vos documents
- Historique de conversation conservé pendant la session

### Utilisation via API (cURL)

Vous pouvez également interroger le système directement via l'API REST :

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Quels sont les principes de base du test logiciel selon ISTQB?\", \"top_k\": 5, \"temperature\": 0.7, \"max_tokens\": 500}"
```

**Paramètres :**
- `question` (requis) : Votre question en langage naturel
- `top_k` (optionnel) : Nombre de chunks à récupérer (défaut: 5)
- `temperature` (optionnel) : Créativité du LLM 0-1 (défaut: 0.7)
- `max_tokens` (optionnel) : Longueur max de la réponse (défaut: 500)

**Réponse JSON :**
```json
{
  "response": "Réponse générée par le LLM...",
  "sources": [
    {
      "text": "Texte du chunk...",
      "source": "document.pdf",
      "chunk_id": 0
    }
  ],
  "num_chunks": 5
}
```

## 📦 Dépendances principales

### Core
- `flask==3.0.0` - Framework web
- `python-dotenv==1.0.0` - Variables d'environnement

### Traitement de documents
- `PyPDF2==3.0.1` - Extraction PDF
- `python-docx==1.1.0` - Extraction Word
- `markdown==3.5.1` - Extraction Markdown

### RAG et embeddings
- `openai>=1.40.0` - Client OpenAI officiel
- `faiss-cpu==1.7.4` - Recherche de similarité vectorielle
- `tiktoken==0.5.1` - Comptage de tokens

### Mode local (optionnel)
- `sentence-transformers==3.3.1` - Embeddings locaux
- `ollama==0.6.1` - Client LLM local
- `torch==2.5.1` - Support PyTorch

## 🔑 Fonctionnalités

### Pipeline RAG complet
- ✅ Upload de documents multiples formats
- ✅ Chunking intelligent avec overlap
- ✅ Vectorisation (OpenAI ou local)
- ✅ Index FAISS pour recherche rapide
- ✅ Retrieval contextuel par similarité
- ✅ Génération de réponses avec LLM
- ✅ Historique de conversation

### Assistant testeur ISTQB
- ✅ Expertise en test logiciel
- ✅ Analyse de spécifications
- ✅ Création de cas de test
- ✅ Stratégies de test
- ✅ Rapports professionnels

### Interface utilisateur
- ✅ Interface web moderne et responsive
- ✅ Navigation par étapes guidée
- ✅ Configuration visible en temps réel
- ✅ Paramètres ajustables (top_k, température, max_tokens)
- ✅ Affichage des sources utilisées

## 🎯 Concepts couverts

- **Chunking** : Découpage intelligent de documents
- **Vectorisation** : Transformation en embeddings
- **Retrieval** : Recherche par similarité vectorielle
- **Assemblage de prompts** : Construction de contexte
- **Génération contrôlée** : LLM avec instructions
- **Réduction des hallucinations** : RAG basé sur documents

## 📦 Stockage des Embeddings

Les vecteurs d'embeddings générés sont stockés localement dans le dossier `data/` :

### Fichiers d'index

1. **`data/faiss_index.bin`**
   - Contient l'index FAISS avec tous les vecteurs d'embeddings
   - C'est ici que FAISS effectue ses recherches ultra-rapides de similarité
   - Format binaire optimisé pour les performances

2. **`data/index_metadata.pkl`**
   - Contient les métadonnées associées aux vecteurs
   - Texte original des chunks
   - Sources des documents
   - Informations de traçabilité (chunk_id, tokens, etc.)

### Processus d'indexation

1. Découpage des documents en chunks
2. Génération d'un embedding (vecteur) pour chaque chunk via OpenAI ou Sentence Transformers
3. Stockage de tous les vecteurs dans l'index FAISS (`faiss_index.bin`)
4. Sauvegarde des textes originaux et métadonnées (`index_metadata.pkl`)

### Processus de recherche

1. Transformation de votre question en vecteur
2. FAISS recherche les vecteurs les plus similaires dans l'index
3. Récupération des chunks correspondants depuis les métadonnées
4. Génération de la réponse par le LLM basée sur ces chunks

> 💡 **Persistance** : Ces fichiers persistent entre les sessions - vous pouvez fermer l'application et l'index sera automatiquement rechargé au redémarrage.

## 📝 Configuration avancée

### Paramètres de chunking
- `chunk_size` : Taille des chunks (défaut: 500 tokens)
- `chunk_overlap` : Chevauchement (défaut: 50 tokens)

### Paramètres de recherche
- `top_k` : Nombre de chunks à récupérer (défaut: 5)
- `temperature` : Créativité du LLM (0-1, défaut: 0.7)
- `max_tokens` : Longueur maximale de la réponse (défaut: 500)

---

© 2025 CFTL JTIA - Paris
