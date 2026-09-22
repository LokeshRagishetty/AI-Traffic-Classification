import pytest
from fastapi.testclient import TestClient
from main import app
from models.traffic import FlowForScheduling
from services.scheduler_service import simulate_fifo, simulate_priority

client = TestClient(app)

def get_test_flows():
    return [
        FlowForScheduling(flowId="1", trafficClass="Web Browsing", priority="Medium", packetCount=100, averagePacketSize=1500.0, arrivalOrder=1),
        FlowForScheduling(flowId="2", trafficClass="Gaming", priority="Critical", packetCount=50, averagePacketSize=200.0, arrivalOrder=2),
        FlowForScheduling(flowId="3", trafficClass="File Transfer", priority="Low", packetCount=200, averagePacketSize=1500.0, arrivalOrder=3),
        FlowForScheduling(flowId="4", trafficClass="VoIP", priority="Critical", packetCount=20, averagePacketSize=100.0, arrivalOrder=4),
        FlowForScheduling(flowId="5", trafficClass="Video Streaming", priority="High", packetCount=150, averagePacketSize=1300.0, arrivalOrder=5),
    ]

def test_fifo_preserves_arrival_order():
    flows = get_test_flows()
    result = simulate_fifo(flows, 1000)
    assert result.serviceOrder == ["1", "2", "3", "4", "5"]
    assert len(result.results) == 5
    for r in result.results:
        assert r.completed == True

def test_priority_orders_by_criticality():
    flows = get_test_flows()
    result = simulate_priority(flows, 1000)
    # Critical (2, 4), High (5), Medium (1), Low (3)
    # Between 2 and 4, 2 has arrivalOrder 2 and 4 has arrivalOrder 4, so 2 should be before 4
    assert result.serviceOrder == ["2", "4", "5", "1", "3"]

def test_fifo_exhausts_capacity():
    flows = get_test_flows()
    # Flow 1 (100) + Flow 2 (50) = 150. Service capacity = 120.
    result = simulate_fifo(flows, 120)
    # Flow 1 and 2 get serviced. 3, 4, 5 do not.
    assert result.serviceOrder == ["1", "2"]
    
    assert result.results[0].flowId == "1"
    assert result.results[0].packetsServed == 100
    assert result.results[0].completed == True
    
    assert result.results[1].flowId == "2"
    assert result.results[1].packetsServed == 20
    assert result.results[1].completed == False
    
    assert result.results[2].packetsServed == 0
    assert result.results[2].completed == False

def test_priority_exhausts_capacity():
    flows = get_test_flows()
    # Flow 2 (Critical, 50) + Flow 4 (Critical, 20) + Flow 5 (High, 150). Total = 220. Capacity = 100
    result = simulate_priority(flows, 100)
    # Flow 2 completely served (50). Flow 4 completely served (20). Flow 5 gets 30.
    assert result.serviceOrder == ["2", "4", "5"]
    
    # Check results in the returned order (which matches the sorted input for priority)
    assert result.results[0].flowId == "2"
    assert result.results[0].packetsServed == 50
    assert result.results[0].completed == True
    
    assert result.results[1].flowId == "4"
    assert result.results[1].packetsServed == 20
    assert result.results[1].completed == True
    
    assert result.results[2].flowId == "5"
    assert result.results[2].packetsServed == 30
    assert result.results[2].completed == False
    
    # 1 and 3 get 0
    assert result.results[3].flowId == "1"
    assert result.results[3].packetsServed == 0
    
    assert result.results[4].flowId == "3"
    assert result.results[4].packetsServed == 0

def test_api_scheduling():
    payload = {
        "flows": [f.model_dump() for f in get_test_flows()],
        "serviceCapacity": 1000
    }
    response = client.post("/api/schedule/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "fifo" in data
    assert "priority" in data
    
    assert data["fifo"]["serviceOrder"] == ["1", "2", "3", "4", "5"]
    assert data["priority"]["serviceOrder"] == ["2", "4", "5", "1", "3"]

def test_api_empty_flows_rejected():
    response = client.post("/api/schedule/simulate", json={"flows": [], "serviceCapacity": 1000})
    assert response.status_code == 400
