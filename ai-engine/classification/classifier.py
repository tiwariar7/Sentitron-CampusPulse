from transformers import pipeline
import os

try:
    import torch
    device = 0 if torch.cuda.is_available() else -1
except ImportError:
    device = -1

class ComplaintClassifier:
    def __init__(self):
        # Using a smaller model for faster execution on CPU/GPU
        # valhalla/distilbart-mnli-12-1 is a good lightweight zero-shot model
        self.model_name = os.getenv("CLASSIFICATION_MODEL", "valhalla/distilbart-mnli-12-1")
        self.classifier = pipeline("zero-shot-classification", model=self.model_name, device=device)
        self.candidate_labels = [
            "Academic", "Infrastructure", "Hostel", "Food", 
            "Financial", "Security", "Other"
        ]

    def classify(self, text: str) -> str:
        if not text:
            return "Other"
        
        try:
            result = self.classifier(text, self.candidate_labels)
            return result['labels'][0]
        except Exception as e:
            print(f"Classification failed: {e}")
            return "Unknown"

# Singleton instance
classifier_pipeline = ComplaintClassifier()
