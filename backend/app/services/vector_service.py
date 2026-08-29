import json
import math
import hashlib
from datetime import datetime
from config import CHROMADB_HOST, CHROMADB_PORT

class VectorService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.ef = None
        self.in_memory_store = [] # Fallback incident memory store

    def _connect(self):
        if self.collection is not None:
            return True
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            self.client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            self.collection = self.client.get_or_create_collection(
                name="loadmind_failures",
                embedding_function=self.ef
            )
            return True
        except Exception as e:
            # Fallback quietly to internal similarity engine
            return False

    def add_incident(self, incident_id: str, signature_text: str, metadata: dict):
        # 1. Store in internal memory
        existing = next((item for item in self.in_memory_store if item["id"] == incident_id), None)
        if not existing:
            self.in_memory_store.append({
                "id": incident_id,
                "document": signature_text,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat()
            })
            
        # 2. Also push to ChromaDB if reachable
        if self._connect():
            try:
                self.collection.add(
                    documents=[signature_text],
                    metadatas=[metadata],
                    ids=[incident_id]
                )
            except Exception as e:
                pass
        return True

    def query_similar_incidents(self, signature_text: str, n_results: int = 3):
        if self._connect():
            try:
                results = self.collection.query(
                    query_texts=[signature_text],
                    n_results=n_results
                )
                formatted = []
                if results and 'documents' in results and results['documents']:
                    for i in range(len(results['documents'][0])):
                        formatted.append({
                            "id": results['ids'][0][i],
                            "document": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i],
                            "distance": results['distances'][0][i] if 'distances' in results else None
                        })
                if formatted:
                    return formatted
            except Exception as e:
                pass

        # Fallback Jaccard token / keyword similarity engine for standalone & offline runs
        query_tokens = set(signature_text.lower().replace(":", " ").replace(",", " ").split())
        scored = []
        for item in self.in_memory_store:
            item_tokens = set(item["document"].lower().replace(":", " ").replace(",", " ").split())
            intersection = query_tokens.intersection(item_tokens)
            union = query_tokens.union(item_tokens)
            similarity = len(intersection) / len(union) if union else 0
            scored.append((similarity, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": item["id"],
                "document": item["document"],
                "metadata": item["metadata"],
                "distance": round(1.0 - sim, 3)
            }
            for sim, item in scored[:n_results]
        ]

vector_service = VectorService()

