import pytest
from fastapi.testclient import TestClient
from main import app
from services.traffic_generator import generate_synthetic_traffic

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "AI Network Traffic Classification API"}

def test_generate_traffic_valid_count():
    response = client.post("/api/traffic/generate", json={"count": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 10
    assert len(data["flows"]) == 10

def test_generate_traffic_min_count():
    response = client.post("/api/traffic/generate", json={"count": 1})
    assert response.status_code == 200
    assert response.json()["count"] == 1

def test_generate_traffic_max_count():
    response = client.post("/api/traffic/generate", json={"count": 1000})
    assert response.status_code == 200
    assert response.json()["count"] == 1000

def test_generate_traffic_invalid_counts():
    # count = 0
    assert client.post("/api/traffic/generate", json={"count": 0}).status_code == 422
    # count = -1
    assert client.post("/api/traffic/generate", json={"count": -1}).status_code == 422
    # count = 1001
    assert client.post("/api/traffic/generate", json={"count": 1001}).status_code == 422

def test_traffic_generator_reproducibility():
    flows1 = generate_synthetic_traffic(count=100, seed=42)
    flows2 = generate_synthetic_traffic(count=100, seed=42)
    
    # Check that they match
    assert [f.flowId for f in flows1] == [f.flowId for f in flows2]
    assert [f.groundTruthClass for f in flows1] == [f.groundTruthClass for f in flows2]

def test_traffic_generator_different_seeds():
    flows1 = generate_synthetic_traffic(count=100, seed=42)
    flows2 = generate_synthetic_traffic(count=100, seed=43)
    
    assert [f.flowId for f in flows1] != [f.flowId for f in flows2]

def test_all_classes_generated():
    # Generate a large number of flows to ensure all classes appear
    flows = generate_synthetic_traffic(count=1000, seed=42)
    classes = set([f.groundTruthClass for f in flows])
    assert classes == {"Gaming", "Video Streaming", "Web Browsing", "File Transfer", "VoIP"}

def test_flow_numeric_validity():
    flows = generate_synthetic_traffic(count=100, seed=42)
    for flow in flows:
        assert flow.packetCount > 0
        assert flow.averagePacketSize > 0
        assert flow.flowDuration > 0
        assert flow.packetsPerSecond > 0
        assert flow.bytesPerSecond > 0
        assert flow.averageInterArrivalTime >= 0
        assert flow.protocol in ["TCP", "UDP"]
