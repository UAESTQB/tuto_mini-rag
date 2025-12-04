from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import json
import time
from datetime import datetime

# Importer les modules RAG
from modules.document_processor import DocumentProcessor
from modules.chunker import TextChunker
from modules.indexer import FAISSIndexer

# Charger les variables d'environnement (override=True pour forcer le rechargement)
load_dotenv(override=True)

# Mode hybride : lire depuis .env
EMBEDDING_MODE = os.environ.get('EMBEDDING_MODE', 'openai').lower()  # 'openai' ou 'local'
LLM_MODE = os.environ.get('LLM_MODE', 'openai').lower()  # 'openai' ou 'local'
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

# Importer conditionnellement les modules locaux
LocalEmbedder = None
LocalLLM = None

if EMBEDDING_MODE == 'local' or LLM_MODE == 'local':
    try:
        if EMBEDDING_MODE == 'local':
            from modules.local_embedder import LocalEmbedder
        if LLM_MODE == 'local':
            from modules.local_llm import LocalLLM
    except ImportError as e:
        print(f"⚠️ Erreur d'import des modules locaux: {e}")
        print("💡 Pour utiliser le mode local, installez : pip install sentence-transformers ollama torch")
        if EMBEDDING_MODE == 'local':
            print("   Passage au mode OpenAI pour les embeddings")
            EMBEDDING_MODE = 'openai'
        if LLM_MODE == 'local':
            print("   Passage au mode OpenAI pour le LLM")
            LLM_MODE = 'openai'

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
INDEX_PATH = os.path.join(DATA_FOLDER, 'faiss_index.bin')
METADATA_PATH = os.path.join(DATA_FOLDER, 'index_metadata.pkl')
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'md'}
MAX_FILE_SIZE = 256 * 1024 * 1024  # 256 MB

# Mode hybride : lire depuis .env
EMBEDDING_MODE = os.environ.get('EMBEDDING_MODE', 'openai').lower()  # 'openai' ou 'local'
LLM_MODE = os.environ.get('LLM_MODE', 'openai').lower()  # 'openai' ou 'local'
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

print(f"🔧 Configuration:")
print(f"  - Embeddings: {EMBEDDING_MODE}")
print(f"  - LLM: {LLM_MODE}")
if LLM_MODE == 'local':
    print(f"  - Modèle Ollama: {OLLAMA_MODEL}")
else:
    print(f"  - Modèle OpenAI: {OPENAI_MODEL}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Créer les dossiers nécessaires
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# Instances globales
indexer = None
local_embedder = None
local_llm = None

# Initialiser les modèles locaux si nécessaire
if EMBEDDING_MODE == 'local' and LocalEmbedder:
    try:
        print("📥 Chargement de Sentence Transformers...")
        local_embedder = LocalEmbedder(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        print("✅ Sentence Transformers chargé")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de Sentence Transformers: {e}")
        EMBEDDING_MODE = 'openai'

if LLM_MODE == 'local' and LocalLLM:
    try:
        print("📥 Initialisation d'Ollama...")
        local_llm = LocalLLM(model=OLLAMA_MODEL)
        print("✅ Ollama initialisé")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation d'Ollama: {e}")
        LLM_MODE = 'openai'

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_uploaded_files():
    """Récupère la liste des fichiers uploadés avec leurs métadonnées"""
    files_list = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            # Ignorer les fichiers .gitkeep
            if filename == '.gitkeep':
                continue
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                file_stat = os.stat(filepath)
                files_list.append({
                    'name': filename,
                    'size': file_stat.st_size,
                    'date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    return sorted(files_list, key=lambda x: x['date'], reverse=True)

def delete_indexes():
    """Supprime les fichiers d'index FAISS et métadonnées"""
    global indexer
    deleted = []
    
    if os.path.exists(INDEX_PATH):
        os.remove(INDEX_PATH)
        deleted.append('faiss_index.bin')
    
    if os.path.exists(METADATA_PATH):
        os.remove(METADATA_PATH)
        deleted.append('index_metadata.pkl')
    
    # Réinitialiser l'indexer global
    indexer = None
    
    return deleted

@app.route('/')
def index():
    """
    Page d'accueil du tutoriel Mini-RAG.
    Affiche la présentation du projet, les objectifs pédagogiques,
    la stack technique et les prérequis nécessaires.
    """
    files = get_uploaded_files()
    has_documents = len(files) > 0
    has_index = os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH)
    return render_template('index.html', 
                         has_documents=has_documents, 
                         has_index=has_index,
                         llm_mode=LLM_MODE,
                         embedding_mode=EMBEDDING_MODE,
                         ollama_model=OLLAMA_MODEL if LLM_MODE == 'local' else None,
                         openai_model=OPENAI_MODEL if LLM_MODE == 'openai' else None)

@app.route('/prompt-library')
def prompt_library():
    """
    Bibliothèque de Prompts : Guide pour créer des prompts efficaces.
    Explique la structure en 6 éléments d'un bon prompt pour l'IA générative
    et fournit des exemples pratiques pour la génération de critères d'acceptation.
    """
    files = get_uploaded_files()
    has_documents = len(files) > 0
    has_index = os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH)
    return render_template('prompt_library.html', 
                         has_documents=has_documents, 
                         has_index=has_index,
                         llm_mode=LLM_MODE,
                         embedding_mode=EMBEDDING_MODE,
                         ollama_model=OLLAMA_MODEL if LLM_MODE == 'local' else None,
                         openai_model=OPENAI_MODEL if LLM_MODE == 'openai' else None)

@app.route('/upload')
def upload():
    """
    Étape 1 : Page d'upload de documents.
    Permet de téléverser des fichiers (PDF, DOCX, TXT, MD)
    et affiche la liste des documents déjà uploadés.
    """
    files = get_uploaded_files()
    has_index = os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH)
    return render_template('upload.html', 
                         files=files, 
                         has_documents=len(files) > 0, 
                         has_index=has_index,
                         llm_mode=LLM_MODE,
                         embedding_mode=EMBEDDING_MODE,
                         ollama_model=OLLAMA_MODEL if LLM_MODE == 'local' else None,
                         openai_model=OPENAI_MODEL if LLM_MODE == 'openai' else None)

@app.route('/indexation')
def indexation():
    """
    Étape 2 : Page d'indexation des documents.
    Configure les paramètres de chunking et lance la création
    de l'index vectoriel FAISS pour la recherche.
    """
    files = get_uploaded_files()
    index_exists = os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH)
    
    index_stats = None
    if index_exists and indexer and indexer.index is not None:
        index_stats = indexer.get_stats()
    
    return render_template('indexation.html', 
                         file_count=len(files), 
                         index_exists=index_exists,
                         index_stats=index_stats,
                         has_documents=len(files) > 0,
                         has_index=index_exists,
                         llm_mode=LLM_MODE,
                         embedding_mode=EMBEDDING_MODE,
                         ollama_model=OLLAMA_MODEL if LLM_MODE == 'local' else None,
                         openai_model=OPENAI_MODEL if LLM_MODE == 'openai' else None)

@app.route('/search')
def search():
    """
    Étape 3 : Page de recherche et utilisation des documents.
    Interface de chat avec l'assistant testeur ISTQB qui répond
    aux questions en se basant sur les documents indexés.
    """
    files = get_uploaded_files()
    has_index = os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH)
    return render_template('search.html', 
                         has_documents=len(files) > 0, 
                         has_index=has_index,
                         llm_mode=LLM_MODE,
                         embedding_mode=EMBEDDING_MODE,
                         ollama_model=OLLAMA_MODEL if LLM_MODE == 'local' else None,
                         openai_model=OPENAI_MODEL if LLM_MODE == 'openai' else None)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    API POST : Upload d'un fichier.
    Vérifie le type de fichier, l'enregistre dans le dossier uploads/
    et retourne les métadonnées du fichier uploadé.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    
    if not file.filename or file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'Type de fichier non autorisé. Extensions autorisées: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    filename = secure_filename(file.filename)
    
    # Vérifier si le fichier existe déjà
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return jsonify({'error': f'Le fichier "{filename}" existe déjà. Veuillez le supprimer d\'abord ou renommer votre fichier.'}), 409
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    file_stat = os.stat(filepath)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'size': file_stat.st_size,
        'date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/files', methods=['GET'])
def list_files():
    """
    API GET : Liste des fichiers uploadés.
    Retourne tous les fichiers présents dans uploads/
    avec leurs métadonnées (nom, taille, date).
    """
    files = get_uploaded_files()
    return jsonify({'files': files})

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    API DELETE : Suppression d'un fichier spécifique.
    Supprime le fichier et nettoie les index FAISS si c'était
    le dernier document uploadé.
    """
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    
    if os.path.exists(filepath):
        os.remove(filepath)
        
        # Si c'était le dernier fichier, supprimer aussi les index
        remaining_files = get_uploaded_files()
        if len(remaining_files) == 0:
            deleted_indexes = delete_indexes()
            if deleted_indexes:
                return jsonify({
                    'success': True, 
                    'message': f'Fichier {filename} supprimé. Index supprimés également (dernier document).',
                    'indexes_deleted': deleted_indexes
                })
        
        return jsonify({'success': True, 'message': f'Fichier {filename} supprimé'})
    else:
        return jsonify({'error': 'Fichier non trouvé'}), 404

@app.route('/api/delete-all', methods=['DELETE'])
def delete_all_files():
    """
    API DELETE : Suppression de tous les fichiers.
    Supprime tous les documents uploadés et les index FAISS associés.
    Réinitialise complètement le système.
    """
    try:
        deleted_count = 0
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    deleted_count += 1
        
        # Supprimer aussi les index
        deleted_indexes = delete_indexes()
        
        message = f'{deleted_count} fichier(s) supprimé(s)'
        if deleted_indexes:
            message += f' et {len(deleted_indexes)} index supprimé(s)'
        
        return jsonify({
            'success': True, 
            'message': message, 
            'count': deleted_count,
            'indexes_deleted': deleted_indexes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-index', methods=['DELETE'])
def delete_index_only():
    """
    API DELETE : Suppression de l'index FAISS uniquement.
    Supprime les fichiers d'index sans toucher aux documents uploadés.
    Utile pour ré-indexer avec un mode d'embedding différent.
    """
    try:
        deleted_indexes = delete_indexes()
        
        if deleted_indexes:
            return jsonify({
                'success': True,
                'message': f'Index FAISS supprimé avec succès ({", ".join(deleted_indexes)})',
                'indexes_deleted': deleted_indexes
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Aucun index à supprimer'
            }), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/index', methods=['POST'])
def create_index():
    """
    API POST : Création de l'index FAISS.
    Extrait le texte, découpe en chunks, génère les embeddings
    (OpenAI ou local) et crée l'index vectoriel pour la recherche.
    """
    global indexer, local_embedder
    
    try:
        # Récupérer la configuration
        config = request.get_json()
        chunk_size = config.get('chunk_size', 500)
        chunk_overlap = config.get('chunk_overlap', 50)
        embedding_model = config.get('embedding_model', 'text-embedding-3-small')
        
        start_time = time.time()
        
        # 1. Traiter les documents
        print("Étape 1: Extraction du texte...")
        processor = DocumentProcessor()
        documents = processor.process_directory(UPLOAD_FOLDER)
        
        successful_docs = [doc for doc in documents if doc.get('success')]
        if not successful_docs:
            return jsonify({'success': False, 'error': 'Aucun document valide à indexer'}), 400
        
        # 2. Chunking
        print("Étape 2: Découpage en chunks...")
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.chunk_documents(successful_docs)
        
        if not chunks:
            return jsonify({'success': False, 'error': 'Aucun chunk généré'}), 400
        
        # 3. Créer l'index FAISS (mode hybride)
        print(f"Étape 3: Création de l'index FAISS (mode {EMBEDDING_MODE})...")
        
        if EMBEDDING_MODE == 'local':
            # Mode local
            if not local_embedder:
                return jsonify({'success': False, 'error': 'Embedder local non initialisé'}), 500
            indexer = FAISSIndexer(mode='local', local_embedder=local_embedder)
            model_name = "local (Sentence Transformers)"
        else:
            # Mode OpenAI
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return jsonify({'success': False, 'error': 'Clé API OpenAI non configurée'}), 500
            indexer = FAISSIndexer(api_key=api_key, model=embedding_model, mode='openai')
            model_name = embedding_model
        
        index_result = indexer.create_index(chunks)
        
        if not index_result.get('success'):
            return jsonify({'success': False, 'error': index_result.get('error', 'Erreur inconnue')}), 500
        
        # 4. Sauvegarder l'index
        print("Étape 4: Sauvegarde de l'index...")
        indexer.save_index(INDEX_PATH, METADATA_PATH)
        
        elapsed_time = round(time.time() - start_time, 2)
        
        return jsonify({
            'success': True,
            'documents_processed': len(successful_docs),
            'total_chunks': len(chunks),
            'total_vectors': index_result['total_chunks'],
            'model': model_name,
            'mode': EMBEDDING_MODE,
            'elapsed_time': elapsed_time
        })
        
    except Exception as e:
        print(f"Erreur lors de l'indexation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/index-stats', methods=['GET'])
def get_index_stats():
    """
    API GET : Statistiques de l'index FAISS.
    Retourne le nombre de vecteurs, chunks, sources indexées
    et le modèle d'embedding utilisé.
    """
    global indexer, local_embedder
    
    try:
        if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
            if indexer is None or indexer.index is None:
                # Charger l'index selon le mode
                if EMBEDDING_MODE == 'local':
                    if not local_embedder:
                        return jsonify({'indexed': False, 'error': 'Embedder local non initialisé'})
                    indexer = FAISSIndexer(mode='local', local_embedder=local_embedder)
                else:
                    api_key = os.environ.get('OPENAI_API_KEY')
                    indexer = FAISSIndexer(api_key=api_key, mode='openai')
                
                indexer.load_index(INDEX_PATH, METADATA_PATH)
            
            stats = indexer.get_stats()
            stats['embedding_mode'] = EMBEDDING_MODE
            return jsonify(stats)
        else:
            return jsonify({'indexed': False})
    except Exception as e:
        print(f"Erreur lors de la récupération des stats: {str(e)}")
        return jsonify({'indexed': False, 'error': str(e)})

@app.route('/api/search', methods=['POST'])
def search_documents():
    """
    API POST : Recherche RAG et génération de réponse.
    Effectue une recherche par similarité dans FAISS, récupère
    les chunks pertinents et génère une réponse contextuelle
    avec l'assistant testeur ISTQB (OpenAI ou Ollama).
    Conserve l'historique de conversation pour un dialogue continu.
    """
    global indexer, local_embedder, local_llm
    
    try:
        # Récupérer les paramètres
        data = request.get_json()
        question = data.get('question', '')
        conversation_history = data.get('conversation_history', [])
        top_k = data.get('top_k', 5)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 500)
        custom_system_prompt = data.get('system_prompt', '')
        
        if not question:
            return jsonify({'success': False, 'error': 'Question non fournie'}), 400
        
        # Vérifier que l'index est chargé
        if indexer is None or indexer.index is None:
            if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
                # Charger selon le mode d'embedding
                if EMBEDDING_MODE == 'local':
                    if not local_embedder:
                        return jsonify({'success': False, 'error': 'Embedder local non initialisé'}), 500
                    indexer = FAISSIndexer(mode='local', local_embedder=local_embedder)
                else:
                    api_key = os.environ.get('OPENAI_API_KEY')
                    indexer = FAISSIndexer(api_key=api_key, mode='openai')
                
                indexer.load_index(INDEX_PATH, METADATA_PATH)
            else:
                return jsonify({'success': False, 'error': 'Index non disponible. Veuillez d\'abord indexer des documents.'}), 400
        
        # 1. Rechercher les chunks pertinents
        search_results = indexer.search(question, top_k=top_k)
        
        if not search_results:
            return jsonify({'success': False, 'error': 'Aucun résultat trouvé'}), 404
        
        # 2. Construire le contexte
        context = "\n\n".join([
            f"[Document: {result['source']}]\n{result['text']}"
            for result in search_results
        ])
        
        # 3. Générer la réponse selon le mode LLM
        # Utiliser le prompt système personnalisé s'il est fourni, sinon utiliser le prompt par défaut
        if custom_system_prompt:
            system_prompt = custom_system_prompt
        else:
            system_prompt = """Tu es un testeur certifié ISTQB (International Software Testing Qualifications Board) avec une expertise approfondie en assurance qualité logicielle. 

        Ton rôle est d'assister dans toutes les activités de test selon le processus ISTQB :

        1. **Analyse des tests** : Identifier les conditions de test à partir des exigences et spécifications
        2. **Conception des tests** : Créer des cas de test détaillés, des scénarios et des données de test
        3. **Implémentation des tests** : Préparer les scripts de test et l'environnement de test
        4. **Exécution des tests** : Définir les procédures d'exécution et les critères de validation

        Tu bases tes réponses sur les documents fournis et tu appliques les bonnes pratiques ISTQB. Tu peux :
        - Analyser des spécifications pour identifier les cas de test
        - Créer des cas de test détaillés avec préconditions, étapes et résultats attendus
        - Proposer des stratégies de test adaptées
        - Identifier les risques et prioriser les tests
        - Rédiger des rapports de test professionnels

        Si l'information n'est pas dans les documents, tu le dis clairement et tu proposes une approche basée sur les standards ISTQB."""

        if LLM_MODE == 'local':
            # Mode local avec Ollama
            if not local_llm:
                return jsonify({'success': False, 'error': 'LLM local non initialisé'}), 500
            
            # Construire le prompt avec l'historique de conversation
            conversation_context = ""
            if len(conversation_history) > 1:  # S'il y a de l'historique (plus que la question actuelle)
                conversation_context = "\n\nHistorique de la conversation :\n"
                for i, msg in enumerate(conversation_history[:-1]):  # Exclure la dernière question
                    role = "Utilisateur" if msg['role'] == 'user' else "Assistant"
                    conversation_context += f"{role}: {msg['content']}\n"
            
            prompt = f"""{system_prompt}

            Contexte documentaire :
            {context}
            {conversation_context}

            Question : {question}

            Réponds en tant que testeur ISTQB certifié, en te basant sur le contexte fourni et l'historique de conversation."""
            
            answer = local_llm.generate_simple(
                prompt=prompt,
                temperature=temperature
            )
            llm_model = OLLAMA_MODEL
            
            # Estimation approximative des tokens pour Ollama (1 token ≈ 4 caractères)
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(answer) // 4
            total_tokens = prompt_tokens + completion_tokens
        else:
            # Mode OpenAI avec historique de conversation
            from openai import OpenAI
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return jsonify({'success': False, 'error': 'Clé API OpenAI non configurée'}), 500
            
            client = OpenAI(api_key=api_key)
            
            # Construire les messages avec l'historique
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            
            # Ajouter le contexte documentaire comme premier message utilisateur
            messages.append({
                "role": "user",
                "content": f"Contexte documentaire disponible :\n{context}"
            })
            
            messages.append({
                "role": "assistant",
                "content": "J'ai bien pris connaissance du contexte documentaire. Je suis prêt à répondre à vos questions en tant que testeur ISTQB certifié."
            })
            
            # Ajouter l'historique de conversation (limiter aux 10 derniers échanges pour ne pas dépasser les tokens)
            recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
            messages.extend(recent_history)
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            answer = response.choices[0].message.content
            llm_model = OPENAI_MODEL
            
            # Récupérer les tokens utilisés depuis OpenAI
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
        
        return jsonify({
            'success': True,
            'answer': answer,
            'sources': search_results,
            'llm_mode': LLM_MODE,
            'llm_model': llm_model,
            'embedding_mode': EMBEDDING_MODE,
            'tokens': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens
            }
        })
        
    except Exception as e:
        print(f"Erreur lors de la recherche: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Charger l'index au démarrage si il existe
    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
        try:
            if EMBEDDING_MODE == 'local':
                if local_embedder:
                    indexer = FAISSIndexer(mode='local', local_embedder=local_embedder)
                    indexer.load_index(INDEX_PATH, METADATA_PATH)
                    print(f"Index FAISS chargé avec succès (mode {EMBEDDING_MODE})!")
            else:
                api_key = os.environ.get('OPENAI_API_KEY')
                if api_key:
                    indexer = FAISSIndexer(api_key=api_key, mode='openai')
                    indexer.load_index(INDEX_PATH, METADATA_PATH)
                    print(f"Index FAISS chargé avec succès (mode {EMBEDDING_MODE})!")
        except Exception as e:
            print(f"Erreur lors du chargement de l'index: {str(e)}")
    
    # Compatible avec tous les OS
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
