"""
Module LLM local avec Ollama
Alternative locale à OpenAI GPT
"""

from typing import List, Dict
import ollama


class LocalLLM:
    """Classe pour utiliser Ollama comme LLM local"""
    
    def __init__(self, model: str = "llama3.2:3b"):
        """
        Initialize le LLM local
        
        Args:
            model: Nom du modèle Ollama (llama3.2:3b, mistral:7b, etc.)
        """
        self.model = model
        print(f"Utilisation du modèle local: {model}")
        
        # Vérifier que le modèle est disponible
        try:
            models_response = ollama.list()
            available = []
            
            # Extraire la liste de modèles
            if hasattr(models_response, 'models'):
                model_list = models_response.models
            elif isinstance(models_response, dict):
                model_list = models_response.get('models', [])
            else:
                model_list = []
            
            # Extraire les noms des modèles
            for m in model_list:
                if hasattr(m, 'model'):
                    available.append(m.model)
                elif isinstance(m, dict):
                    name = m.get('model') or m.get('name')
                    if name:
                        available.append(name)
            
            if available and model not in available:
                print(f"⚠️ Modèle {model} non trouvé. Modèles disponibles: {available}")
                print(f"Téléchargez-le avec: ollama pull {model}")
        except Exception as e:
            print(f"⚠️ Impossible de vérifier les modèles Ollama: {e}")
    
    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        Génère une réponse à partir de messages
        
        Args:
            messages: Liste de messages au format [{"role": "user", "content": "..."}]
            temperature: Température de génération (0-1)
            
        Returns:
            Réponse générée
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": 1000  # Limite de tokens
                }
            )
            return response['message']['content']
        except Exception as e:
            return f"Erreur lors de la génération: {str(e)}"
    
    def generate_simple(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Génère une réponse simple à partir d'un prompt
        
        Args:
            prompt: Prompt de génération
            temperature: Température de génération
            
        Returns:
            Réponse générée
        """
        messages = [{"role": "user", "content": prompt}]
        return self.generate_response(messages, temperature)
