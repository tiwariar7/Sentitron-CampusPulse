from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import os
import uuid
import logging

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "complaints"
VECTOR_SIZE = 384  # from all-MiniLM-L6-v2

class QdrantService:
    def __init__(self):
        # Check if we should run in-memory for testing
        if QDRANT_URL == "memory":
            self.client = QdrantClient(":memory:")
            logger.info("Using Qdrant in-memory client.")
        else:
            try:
                # Set a 2-second timeout to prevent blocking during server boot
                self.client = QdrantClient(url=QDRANT_URL, timeout=2.0)
                logger.info(f"Connected to Qdrant at {QDRANT_URL}")
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant at {QDRANT_URL}. Falling back to memory. Error: {e}")
                self.client = QdrantClient(":memory:")
                
        try:
            self._ensure_collection()
        except Exception as e:
            logger.warning(f"Failed to ensure collection on Qdrant client at {QDRANT_URL}. Falling back to memory. Error: {e}")
            self.client = QdrantClient(":memory:")
            self._ensure_collection()
        
    def _ensure_collection(self):
        if not self.client.collection_exists(collection_name=COLLECTION_NAME):
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def insert_complaint(self, text: str, category: str, embedding: list, complaint_id: int):
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": text,
                        "category": category,
                        "complaint_id": complaint_id
                    }
                )
            ]
        )
        return point_id
        
    def find_similar(self, embedding: list, limit: int = 5, score_threshold: float = 0.8):
        """Find semantic duplicates/similar complaints using modern query_points endpoint"""
        search_result = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        return search_result.points

# Singleton instance
qdrant_service = QdrantService()
