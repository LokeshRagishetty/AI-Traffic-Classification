import pytest
from fastapi.testclient import TestClient
from main import app
from services.traffic_classifier import classifier
from services.traffic_generator import generate_synthetic_traffic

# The classifier is initialized on app startup, so we need to manually train it for standalone testing
# Or we can trigger the startup event
@pytest.fixture(scope="module", autouse=True)
def setup_classifier():
    classifier.train(num_flows=500) # smaller dataset for fast testing

client = TestClient(app)

def test_model_metrics_available():
    response = client.get("/api/ml/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "confusionMatrix" in data
    assert "classes" in data
    assert len(data["classes"]) == 5
    assert set(data["classes"]) == {"Gaming", "Video Streaming", "Web Browsing", "File Transfer", "VoIP"}

def test_model_classification():
    flows = generate_synthetic_traffic(count=10, seed=42)
    flows_dict = [f.model_dump() for f in flows]
    
    response = client.post("/api/classify", json={"flows": flows_dict})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 10
    
    for result in data["results"]:
        assert "flowId" in result
        assert "predictedClass" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["predictedClass"] in {"Gaming", "Video Streaming", "Web Browsing", "File Transfer", "VoIP"}
        assert "priority" in result
        
        # Verify deterministic priority mapping is correct in API integration
        pred = result["predictedClass"]
        prio = result["priority"]
        if pred in ["Gaming", "VoIP"]:
            assert prio == "Critical"
        elif pred == "Video Streaming":
            assert prio == "High"
        elif pred == "Web Browsing":
            assert prio == "Medium"
        elif pred == "File Transfer":
            assert prio == "Low"

def test_features_used():
    # Verify that flowId, timestamp, and groundTruthClass are NOT in the model's feature names
    feature_names_in = classifier.model.feature_names_in_
    assert "flowId" not in feature_names_in
    assert "timestamp" not in feature_names_in
    assert "groundTruthClass" not in feature_names_in
    
def test_invalid_classification_request():
    # Sending missing fields
    response = client.post("/api/classify", json={"flows": [{"invalid": "data"}]})
    assert response.status_code == 422
