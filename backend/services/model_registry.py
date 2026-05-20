"""
Model version registry.
Exposes active model versions and metadata via GET /api/monitoring/models (admin only).
"""
import os

MODEL_REGISTRY = {
    "classifier": {
        "version":     os.getenv("MODEL_CLASSIFIER_VERSION", "1.0.0"),
        "description": "NLP incident category & severity classifier",
        "framework":   "HuggingFace Transformers",
        "input":       "complaint_text (str)",
        "output":      "category (str)",
        "confidence_threshold": float(os.getenv("INFERENCE_CONFIDENCE_THRESHOLD", "0.70")),
    },
    "embedder": {
        "version":     os.getenv("MODEL_EMBEDDER_VERSION", "1.0.0"),
        "description": "Sentence embedding model for semantic clustering",
        "framework":   "sentence-transformers",
        "model_name":  "all-MiniLM-L6-v2",
        "output_dim":  384,
    },
}


def get_model_info(model_name: str) -> dict:
    return MODEL_REGISTRY.get(model_name, {"error": "Model not found"})


def get_all_models() -> dict:
    return MODEL_REGISTRY
