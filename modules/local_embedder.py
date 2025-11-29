"""
Module d'embeddings local avec Sentence Transformers
Alternative locale à OpenAI Embeddings
"""

from typing import List
from sentence_transformers import SentenceTransformer


class LocalEmbedder:
    """Classe pour générer des embeddings localement avec Sentence Transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize l'embedder local
        
        Args:
            model_name: Nom du modèle Sentence Transformers
                       Options: 
                       - "all-MiniLM-L6-v2" (384 dim, rapide, anglais)
                       - "paraphrase-multilingual-MiniLM-L12-v2" (384 dim, multilingue)
                       - "all-mpnet-base-v2" (768 dim, meilleur mais plus lourd)
        """
        print(f"Chargement du modèle local: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Modèle chargé. Dimension: {self.dimension}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Génère l'embedding d'un texte
        
        Args:
            text: Texte à embedder
            
        Returns:
            Vecteur d'embedding
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Génère les embeddings pour plusieurs textes (plus efficace)
        
        Args:
            texts: Liste de textes à embedder
            
        Returns:
            Liste de vecteurs d'embeddings
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()
