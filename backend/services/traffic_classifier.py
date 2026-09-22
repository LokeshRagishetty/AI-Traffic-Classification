import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import logging

from models.traffic import TrafficFlow, TrafficClassificationResult
from services.traffic_generator import generate_synthetic_traffic
from services.priority_service import assign_priority

logger = logging.getLogger(__name__)

class TrafficClassifier:
    def __init__(self):
        self.model = None
        self.metrics = None
        self.classes = ["Gaming", "Video Streaming", "Web Browsing", "File Transfer", "VoIP"]
        
        # We don't train immediately on init to avoid blocking fast imports if not needed, 
        # but we provide a startup function
        
    def _flows_to_dataframe(self, flows: list[TrafficFlow]) -> pd.DataFrame:
        data = [
            {
                "packetCount": f.packetCount,
                "averagePacketSize": f.averagePacketSize,
                "packetsPerSecond": f.packetsPerSecond,
                "bytesPerSecond": f.bytesPerSecond,
                "flowDuration": f.flowDuration,
                "averageInterArrivalTime": f.averageInterArrivalTime,
                "protocol": f.protocol,
                "sourcePort": f.sourcePort,
                "destinationPort": f.destinationPort,
                "tcpFlagPattern": f.tcpFlagPattern,
                "groundTruthClass": f.groundTruthClass
            }
            for f in flows
        ]
        return pd.DataFrame(data)

    def train(self, num_flows: int = 5000):
        """Train the model with synthetic data."""
        logger.info(f"Generating {num_flows} synthetic flows for training...")
        # 5000 flows total (~1000 per class on average)
        flows = generate_synthetic_traffic(count=num_flows, seed=42)
        df = self._flows_to_dataframe(flows)
        
        # Features and target
        X = df.drop(columns=["groundTruthClass"])
        y = df["groundTruthClass"]
        
        # Ensure we have all 5 classes for demonstration
        
        # Preprocessor for categorical variables
        categorical_features = ["protocol", "tcpFlagPattern"]
        numerical_features = [
            "packetCount", "averagePacketSize", "packetsPerSecond", 
            "bytesPerSecond", "flowDuration", "averageInterArrivalTime", 
            "sourcePort", "destinationPort"
        ]
        
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ],
            remainder="passthrough"  # Keep the numerical features
        )
        
        # ML Pipeline
        self.model = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced"))
        ])
        
        # Train / Test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
        
        logger.info("Training RandomForestClassifier...")
        self.model.fit(X_train, y_train)
        
        # Evaluation
        logger.info("Evaluating model...")
        y_pred = self.model.predict(X_test)
        
        # Sort classes to ensure confusion matrix aligns with self.classes
        sorted_classes = sorted(self.classes)
        
        self.metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
            "classes": sorted_classes,
            "confusionMatrix": confusion_matrix(y_test, y_pred, labels=sorted_classes).tolist()
        }
        
        logger.info("Traffic classifier trained successfully.")

    def predict(self, flows: list[TrafficFlow]) -> list[TrafficClassificationResult]:
        if not self.model:
            raise ValueError("Model is not trained yet.")
        
        # Convert requests to DataFrame
        df = self._flows_to_dataframe(flows)
        # Drop groundTruthClass if it's there
        if "groundTruthClass" in df.columns:
            X = df.drop(columns=["groundTruthClass"])
        else:
            X = df
            
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        results = []
        for i, flow in enumerate(flows):
            # Get the confidence for the predicted class
            pred_class = predictions[i]
            # Find the index of the predicted class in model.classes_
            class_idx = list(self.model.classes_).index(pred_class)
            confidence = probabilities[i][class_idx]
            
            # Deterministically assign priority
            priority = assign_priority(pred_class)
            
            results.append(TrafficClassificationResult(
                flowId=flow.flowId,
                predictedClass=pred_class,
                confidence=float(confidence),
                priority=priority
            ))
            
        return results

    def get_metrics(self) -> dict:
        if not self.metrics:
            raise ValueError("Model is not trained yet.")
        return self.metrics

# Global singleton instance
classifier = TrafficClassifier()
