import pytest
from fastapi.testclient import TestClient
from main import app
from models.traffic import FlowForScheduling
from services.scheduler_service import simulate_fifo, simulate_priority
from services.metrics_service import calculate_metrics

client = TestClient(app)

def get_test_flows():
    return [
        FlowForScheduling(flowId="1", trafficClass="Web Browsing", priority="Medium", packetCount=100, averagePacketSize=1000.0, arrivalOrder=0),
        FlowForScheduling(flowId="2", trafficClass="Gaming", priority="Critical", packetCount=50, averagePacketSize=200.0, arrivalOrder=1),
        FlowForScheduling(flowId="3", trafficClass="File Transfer", priority="Low", packetCount=200, averagePacketSize=1500.0, arrivalOrder=2),
    ]

def test_average_and_max_queue_latency():
    flows = [
        FlowForScheduling(flowId="1", trafficClass="Web", priority="Low", packetCount=100, averagePacketSize=1000.0, arrivalOrder=0),
        FlowForScheduling(flowId="2", trafficClass="Gaming", priority="Critical", packetCount=100, averagePacketSize=1000.0, arrivalOrder=1),
    ]
    flow_map = {f.flowId: f for f in flows}
    
    # FIFO:
    # 1 arrives 0.0. Start 0.0. Done 0.1 (100 * 0.001) -> Delay = 0.0
    # 2 arrives 0.05. Start 0.1. Done 0.2 -> Delay = 0.1 - 0.05 = 0.05
    fifo_result = simulate_fifo(flows, 1000)
    fifo_metrics = calculate_metrics(fifo_result, flow_map, 0.2)
    
    assert fifo_metrics.averageQueueLatency == 0.025
    assert fifo_metrics.maxQueueLatency == 0.05

def test_zero_completed_flows():
    flows = get_test_flows()
    flow_map = {f.flowId: f for f in flows}
    # Capacity = 0 -> nothing served
    fifo_result = simulate_fifo(flows, 0)
    fifo_metrics = calculate_metrics(fifo_result, flow_map, 1.0)
    
    assert fifo_metrics.averageQueueLatency == 0.0
    assert fifo_metrics.maxQueueLatency == 0.0
    assert fifo_metrics.throughputMbps == 0.0
    assert fifo_metrics.packetLossPercentage == 100.0
    assert fifo_metrics.jitter == 0.0

def test_throughput_and_mbps_conversion():
    flows = [FlowForScheduling(flowId="1", trafficClass="Web", priority="Low", packetCount=1000, averagePacketSize=125.0, arrivalOrder=0)]
    flow_map = {f.flowId: f for f in flows}
    # 1000 pkts * 125 bytes = 125,000 bytes = 1,000,000 bits = 1 Megabit
    fifo_result = simulate_fifo(flows, 1000)
    # Simulated horizon artificially set to 0.5s -> 1Mb / 0.5s = 2 Mbps
    fifo_metrics = calculate_metrics(fifo_result, flow_map, 0.5)
    
    assert fifo_metrics.throughputMbps == 2.0

def test_zero_duration_protection():
    flows = [FlowForScheduling(flowId="1", trafficClass="Web", priority="Low", packetCount=0, averagePacketSize=125.0, arrivalOrder=0)]
    flow_map = {f.flowId: f for f in flows}
    fifo_result = simulate_fifo(flows, 1000)
    fifo_metrics = calculate_metrics(fifo_result, flow_map, 0.0) # Zero horizon
    assert fifo_metrics.throughputMbps == 0.0

def test_packet_loss_bounds():
    flows = [FlowForScheduling(flowId="1", trafficClass="Web", priority="Low", packetCount=100, averagePacketSize=125.0, arrivalOrder=0)]
    flow_map = {f.flowId: f for f in flows}
    
    # 0% loss
    metrics_0 = calculate_metrics(simulate_fifo(flows, 100), flow_map, 1.0)
    assert metrics_0.packetLossPercentage == 0.0
    
    # 100% loss
    metrics_100 = calculate_metrics(simulate_fifo(flows, 0), flow_map, 1.0)
    assert metrics_100.packetLossPercentage == 100.0
    
    # 50% loss
    metrics_50 = calculate_metrics(simulate_fifo(flows, 50), flow_map, 1.0)
    assert metrics_50.packetLossPercentage == 50.0

def test_jitter():
    # We will forge a completed flows list to test jitter logic directly
    flows = [
        FlowForScheduling(flowId="1", trafficClass="Web", priority="Low", packetCount=10, averagePacketSize=100.0, arrivalOrder=0),
        FlowForScheduling(flowId="2", trafficClass="Web", priority="Low", packetCount=10, averagePacketSize=100.0, arrivalOrder=1),
        FlowForScheduling(flowId="3", trafficClass="Web", priority="Low", packetCount=10, averagePacketSize=100.0, arrivalOrder=2),
    ]
    flow_map = {f.flowId: f for f in flows}
    
    # Arrival spacing is 0.05
    # Flow 1 arrives 0.0, serves 0.0, delay = 0
    # Flow 2 arrives 0.05, serves 0.05 (idles), delay = 0
    # Flow 3 arrives 0.10, serves 0.10 (idles), delay = 0
    # Jitter should be 0
    res = simulate_fifo(flows, 1000)
    metrics = calculate_metrics(res, flow_map, 1.0)
    assert metrics.jitter == 0.0
    
    # Jitter with 1 flow
    metrics_1 = calculate_metrics(simulate_fifo([flows[0]], 1000), flow_map, 1.0)
    assert metrics_1.jitter == 0.0

def test_repeated_identical_inputs():
    flows = get_test_flows()
    flow_map = {f.flowId: f for f in flows}
    m1 = calculate_metrics(simulate_fifo(flows, 100), flow_map, 1.0)
    m2 = calculate_metrics(simulate_fifo(flows, 100), flow_map, 1.0)
    assert m1.model_dump() == m2.model_dump()

def test_fairness_same_inputs():
    flows = get_test_flows()
    
    # We run the simulation natively to ensure inputs aren't modified
    fifo_res = simulate_fifo(flows, 150)
    prio_res = simulate_priority(flows, 150)
    
    # Assert counts
    assert len(fifo_res.results) == len(prio_res.results)
    
    for i in range(len(flows)):
        # Same requested payload
        f = fifo_res.results[i]
        p = prio_res.results[i]
        
        # Verify it's the exact same items just different scheduling
        assert f.packetsRequested == next(x.packetsRequested for x in prio_res.results if x.flowId == f.flowId)
        assert f.priority == next(x.priority for x in prio_res.results if x.flowId == f.flowId)

def test_api_metrics_compare_schema_and_values():
    payload = {
        "flows": [f.model_dump() for f in get_test_flows()],
        "serviceCapacity": 1000
    }
    response = client.post("/api/metrics/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "fifo" in data
    assert "priority" in data
    
    fifo_m = data["fifo"]
    assert "averageQueueLatency" in fifo_m
    assert "maxQueueLatency" in fifo_m
    assert "throughputMbps" in fifo_m
    assert "packetLossPercentage" in fifo_m
    assert "jitter" in fifo_m
    
    assert fifo_m["averageQueueLatency"] >= 0
    assert fifo_m["packetLossPercentage"] >= 0 and fifo_m["packetLossPercentage"] <= 100
