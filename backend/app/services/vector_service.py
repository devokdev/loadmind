import json
import chromadb
from chromadb.utils import embedding_functions
from config import CHROMADB_HOST, CHROMADB_PORT

class VectorService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.ef = None

    def _connect(self):
        if self.collection is not None:
            return True
        try:
            self.client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            self.collection = self.client.get_or_create_collection(
                name="loadmind_failures",
                embedding_function=self.ef
            )
            return True
        except Exception as e:
            print(f"ChromaDB connection attempt failed: {e}")
            return False

    def add_incident(self, incident_id: str, signature_text: str, metadata: dict):
        if not self._connect():
            print("ChromaDB not available, skipping add_incident")
            return False
        try:
            self.collection.add(
                documents=[signature_text],
                metadatas=[metadata],
                ids=[incident_id]
            )
            return True
        except Exception as e:
            print(f"Failed to add incident to vector memory: {e}")
            return False

    def query_similar_incidents(self, signature_text: str, n_results: int = 3):
        if not self._connect():
            print("ChromaDB not available, skipping query")
            return []
        try:
            results = self.collection.query(
                query_texts=[signature_text],
                n_results=n_results
            )
            # format results nicely
            formatted = []
            if results and 'documents' in results and results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            return formatted
        except Exception as e:
            print(f"Failed to query vector memory: {e}")
            return []

vector_service = VectorService()
