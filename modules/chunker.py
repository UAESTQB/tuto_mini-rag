"""
Module de chunking de documents
Découpe les documents en chunks optimisés pour le RAG
"""

from typing import List, Dict
import tiktoken


class TextChunker:
    """Classe pour découper du texte en chunks avec chevauchement"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, model: str = "gpt-3.5-turbo"):
        """
        Initialize le chunker
        
        Args:
            chunk_size: Nombre de tokens par chunk
            chunk_overlap: Nombre de tokens de chevauchement entre chunks
            model: Modèle OpenAI pour le comptage des tokens
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """Compte le nombre de tokens dans un texte"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, source: str = "") -> List[Dict]:
        """
        Découpe un texte en chunks
        
        Args:
            text: Texte à découper
            source: Nom du fichier source
            
        Returns:
            Liste de dictionnaires contenant les chunks et métadonnées
        """
        # Nettoyer le texte
        text = text.strip()
        if not text:
            return []
        
        # Diviser en paragraphes
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_tokens = self.count_tokens(paragraph)
            
            # Si le paragraphe seul dépasse la taille max, on le découpe par phrases
            if paragraph_tokens > self.chunk_size:
                # Sauvegarder le chunk actuel s'il existe
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'source': source,
                        'tokens': current_tokens,
                        'chunk_id': len(chunks)
                    })
                    current_chunk = ""
                    current_tokens = 0
                
                # Découper le long paragraphe
                sentence_chunks = self._chunk_long_text(paragraph, source, len(chunks))
                chunks.extend(sentence_chunks)
            
            # Si ajouter ce paragraphe dépasse la taille, sauvegarder le chunk actuel
            elif current_tokens + paragraph_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'source': source,
                        'tokens': current_tokens,
                        'chunk_id': len(chunks)
                    })
                
                # Commencer un nouveau chunk avec chevauchement
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + "\n\n" + paragraph
                    current_tokens = self.count_tokens(current_chunk)
                else:
                    current_chunk = paragraph
                    current_tokens = paragraph_tokens
            else:
                # Ajouter le paragraphe au chunk actuel
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens += paragraph_tokens
        
        # Ajouter le dernier chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'source': source,
                'tokens': current_tokens,
                'chunk_id': len(chunks)
            })
        
        return chunks
    
    def _chunk_long_text(self, text: str, source: str, start_id: int) -> List[Dict]:
        """Découpe un texte très long en chunks par phrases"""
        sentences = text.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'source': source,
                        'tokens': current_tokens,
                        'chunk_id': start_id + len(chunks)
                    })
                
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'source': source,
                'tokens': current_tokens,
                'chunk_id': start_id + len(chunks)
            })
        
        return chunks
    
    def _get_overlap(self, text: str) -> str:
        """Récupère les derniers tokens pour le chevauchement"""
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= self.chunk_overlap:
            return text
        
        overlap_tokens = tokens[-self.chunk_overlap:]
        return self.encoding.decode(overlap_tokens)
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Découpe plusieurs documents en chunks
        
        Args:
            documents: Liste de documents avec 'text' et 'filename'
            
        Returns:
            Liste de tous les chunks
        """
        all_chunks = []
        
        for doc in documents:
            if doc.get('success') and doc.get('text'):
                chunks = self.chunk_text(doc['text'], doc.get('filename', 'unknown'))
                all_chunks.extend(chunks)
        
        return all_chunks
