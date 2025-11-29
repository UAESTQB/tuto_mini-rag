"""
Module d'indexation FAISS avec embeddings (OpenAI ou local)
Génère les embeddings et crée un index vectoriel
"""

import os
import json
import pickle
from typing import List, Dict, Tuple
import numpy as np
import faiss
from openai import OpenAI


class FAISSIndexer:
    """Classe pour créer et gérer un index FAISS avec embeddings OpenAI ou locaux"""
    
    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small", 
                 mode: str = "openai", local_embedder=None):
        """
        Initialize l'indexer
        
        Args:
            api_key: Clé API OpenAI (requis si mode='openai')
            model: Modèle d'embedding OpenAI
            mode: 'openai' ou 'local'
            local_embedder: Instance de LocalEmbedder si mode='local'
        """
        self.mode = mode
        
        if mode == "openai":
            if not api_key:
                raise ValueError("API key requise pour le mode OpenAI")
            self.client = OpenAI(api_key=api_key)
            self.model = model
            self.dimension = 1536  # Dimension pour text-embedding-3-small
            if model == "text-embedding-3-large":
                self.dimension = 3072
        else:  # mode == "local"
            if not local_embedder:
                raise ValueError("LocalEmbedder requis pour le mode local")
            self.embedder = local_embedder
            self.dimension = local_embedder.dimension
            self.model = "local"
        
        self.index = None
        self.chunks = []
        self.metadata = []
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Génère l'embedding d'un texte
        
        Args:
            text: Texte à embedder
            
        Returns:
            Vecteur d'embedding
        """
        if self.mode == "openai":
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        else:  # mode == "local"
            return self.embedder.generate_embedding(text)
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Génère des embeddings par batch pour efficacité
        
        Args:
            texts: Liste de textes
            batch_size: Taille des batchs
            
        Returns:
            Liste d'embeddings
        """
        embeddings = []
        
        if self.mode == "openai":
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
        else:  # mode == "local"
            # Le local embedder génère un embedding à la fois
            for text in texts:
                embedding = self.embedder.generate_embedding(text)
                embeddings.append(embedding)
        
        return embeddings
    
    def create_index(self, chunks: List[Dict]) -> Dict:
        """
        Crée un index FAISS à partir des chunks
        
        Args:
            chunks: Liste de chunks avec texte et métadonnées
            
        Returns:
            Statistiques de l'indexation
        """
        if not chunks:
            return {'success': False, 'error': 'Aucun chunk à indexer'}
        
        # Extraire les textes
        texts = [chunk['text'] for chunk in chunks]
        
        # Générer les embeddings
        print(f"Génération de {len(texts)} embeddings...")
        embeddings = self.generate_embeddings_batch(texts)
        
        # Convertir en numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Créer l'index FAISS
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings_array)
        
        # Stocker les chunks et métadonnées
        self.chunks = chunks
        self.metadata = [
            {
                'chunk_id': chunk.get('chunk_id', i),
                'source': chunk.get('source', 'unknown'),
                'tokens': chunk.get('tokens', 0)
            }
            for i, chunk in enumerate(chunks)
        ]
        
        return {
            'success': True,
            'total_chunks': len(chunks),
            'dimension': self.dimension,
            'model': self.model
        }
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Recherche les chunks les plus similaires à une requête
        
        Args:
            query: Texte de recherche
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste des chunks les plus pertinents avec scores
        """
        if self.index is None or len(self.chunks) == 0:
            return []
        
        # Générer l'embedding de la requête
        query_embedding = self.generate_embedding(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Rechercher dans l'index
        distances, indices = self.index.search(query_vector, min(top_k, len(self.chunks)))
        
        # Préparer les résultats
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                results.append({
                    'text': self.chunks[idx]['text'],
                    'source': self.chunks[idx].get('source', 'unknown'),
                    'chunk_id': self.chunks[idx].get('chunk_id', idx),
                    'score': float(distances[0][i]),
                    'rank': i + 1
                })
        
        return results
    
    def save_index(self, index_path: str, metadata_path: str):
        """
        Sauvegarde l'index et les métadonnées
        
        Args:
            index_path: Chemin pour sauvegarder l'index FAISS
            metadata_path: Chemin pour sauvegarder les métadonnées
        """
        if self.index is None:
            raise ValueError("Aucun index à sauvegarder")
        
        # Sauvegarder l'index FAISS
        faiss.write_index(self.index, index_path)
        
        # Sauvegarder les chunks et métadonnées
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'dimension': self.dimension,
                'model': self.model
            }, f)
    
    def load_index(self, index_path: str, metadata_path: str):
        """
        Charge un index et ses métadonnées
        
        Args:
            index_path: Chemin de l'index FAISS
            metadata_path: Chemin des métadonnées
        """
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError("Fichiers d'index introuvables")
        
        # Charger l'index FAISS
        self.index = faiss.read_index(index_path)
        
        # Charger les métadonnées
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']
            self.dimension = data['dimension']
            self.model = data['model']
    
    def get_stats(self) -> Dict:
        """Retourne des statistiques sur l'index"""
        if self.index is None:
            return {'indexed': False}
        
        return {
            'indexed': True,
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'model': self.model,
            'total_chunks': len(self.chunks),
            'sources': list(set(chunk.get('source', 'unknown') for chunk in self.chunks))
        }
