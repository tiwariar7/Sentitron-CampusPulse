from sentence_transformers import SentenceTransformer
import os

class ComplaintEmbedder:
    def __init__(self):
        # Lightweight and fast embedding model
        self.model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(self.model_name)
        
    def embed(self, text: str):
        """Returns the embedding as a list of floats"""
        if not text:
            return [0.0] * 384 # Dimension of all-MiniLM-L6-v2
        
        embedding = self.model.encode(text)
        return embedding.tolist()

# Singleton instance
embedder = ComplaintEmbedder()
