from models.traffic import ScheduleStrategyResult, PerformanceMetrics, FlowForScheduling

def calculate_metrics(strategy_result: ScheduleStrategyResult, original_flows: dict[str, FlowForScheduling], simulation_horizon: float = None) -> PerformanceMetrics:
    completed_flows = [r for r in strategy_result.results if r.completed]
    all_flows = strategy_result.results
    
    # 1. Queue Latency
    # queueDelay = max(0, serviceStartTime - arrivalTime)
    delays = []
    for r in completed_flows:
        delay = max(0.0, r.serviceStartTime - r.arrivalTime)
        delays.append(delay)
        
    avg_queue_latency = sum(delays) / len(delays) if delays else 0.0
    max_queue_latency = max(delays) if delays else 0.0
    
    # 2. Throughput
    # throughput = totalBytesServedWithinSimulationHorizon / commonSimulationDuration
    total_bytes_served = 0.0
    strategy_max_completion = 0.0
    
    for r in strategy_result.results:
        # lookup original flow to get averagePacketSize
        flow = original_flows.get(r.flowId)
        if flow:
            total_bytes_served += (r.packetsServed * flow.averagePacketSize)
        if r.completionTime > strategy_max_completion:
            strategy_max_completion = r.completionTime
            
    # Use provided horizon, or fallback to the strategy's own max completion time
    sim_duration = simulation_horizon if simulation_horizon is not None else strategy_max_completion
    
    # Convert bytes/sec to Mbps (Megabits per second) = (bytes * 8) / 1,000,000
    if sim_duration > 0:
        throughput_bps = total_bytes_served * 8 / sim_duration
        throughput_mbps = throughput_bps / 1_000_000
    else:
        throughput_mbps = 0.0
        
    # 3. Packet Loss
    # packetLoss = packetsRemaining / packetsRequested
    total_requested = sum(r.packetsRequested for r in all_flows)
    total_remaining = sum(r.packetsRemaining for r in all_flows)
    
    packet_loss_percentage = (total_remaining / total_requested * 100) if total_requested > 0 else 0.0
    
    # 4. Jitter
    # jitter = sum(abs(delay[i] - delay[i-1])) / (n - 1)
    completed_flows_sorted = sorted(completed_flows, key=lambda r: r.completionTime)
    n = len(completed_flows_sorted)
    
    if n < 2:
        jitter = 0.0
    else:
        jitter_diffs = []
        for i in range(1, n):
            prev_delay = max(0.0, completed_flows_sorted[i-1].serviceStartTime - completed_flows_sorted[i-1].arrivalTime)
            curr_delay = max(0.0, completed_flows_sorted[i].serviceStartTime - completed_flows_sorted[i].arrivalTime)
            jitter_diffs.append(abs(curr_delay - prev_delay))
        jitter = sum(jitter_diffs) / (n - 1)

    return PerformanceMetrics(
        averageQueueLatency=round(avg_queue_latency, 4),
        maxQueueLatency=round(max_queue_latency, 4),
        throughputMbps=round(throughput_mbps, 4),
        packetLossPercentage=round(packet_loss_percentage, 2),
        jitter=round(jitter, 4)
    )
