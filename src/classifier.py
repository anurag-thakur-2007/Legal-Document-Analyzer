# src/classifier.py

from transformers import pipeline

class ContractClassifier:

    def __init__(self):
        # Load FREE zero-shot classification model
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

        # Define contract types we want to classify
        self.labels = [
            "Service Agreement",
            "Employment Contract",
            "Non-Disclosure Agreement",
            "Consulting Agreement",
            "Lease Agreement"
        ]

    def classify(self, text):
        """
        Classify contract into predefined types
        """

        result = self.classifier(
            sequences=text,
            candidate_labels=self.labels,
            multi_label=False
        )

        return {
            "contract_type": result["labels"][0],
            "confidence": float(result["scores"][0])
        }
