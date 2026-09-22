from models.traffic import FlowForScheduling, ScheduledFlowResult, ScheduleStrategyResult

PRIORITY_WEIGHTS = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1
}

# Simulation time constants
ARRIVAL_INTERVAL = 0.05  # 50 ms between flow arrivals
PROCESS_TIME_PER_PACKET = 0.001  # 1 ms to process a packet

def _run_simulation(flows: list[FlowForScheduling], service_capacity: int) -> ScheduleStrategyResult:
    results = []
    service_order = []
    
    remaining_capacity = service_capacity
    sim_time = 0.0
    
    # Process flows in the order they appear in the list
    for flow in flows:
        arrival_time = flow.arrivalOrder * ARRIVAL_INTERVAL
        
        if remaining_capacity <= 0:
            # Capacity exhausted, this flow gets no service this round
            results.append(ScheduledFlowResult(
                flowId=flow.flowId,
                trafficClass=flow.trafficClass,
                priority=flow.priority,
                arrivalOrder=flow.arrivalOrder,
                serviceOrder=-1, # Not serviced yet
                packetsRequested=flow.packetCount,
                packetsServed=0,
                packetsRemaining=flow.packetCount,
                completed=False,
                arrivalTime=arrival_time,
                serviceStartTime=0.0,
                completionTime=0.0
            ))
            continue
            
        # We can service this flow
        service_order.append(flow.flowId)
        current_service_order = len(service_order)
        
        served = min(flow.packetCount, remaining_capacity)
        remaining = flow.packetCount - served
        
        remaining_capacity -= served
        
        # Advance simulation time to when the flow arrives if we are idle
        service_start_time = max(sim_time, arrival_time)
        processing_duration = served * PROCESS_TIME_PER_PACKET
        completion_time = service_start_time + processing_duration
        
        # Update clock for next flow
        sim_time = completion_time
        
        results.append(ScheduledFlowResult(
            flowId=flow.flowId,
            trafficClass=flow.trafficClass,
            priority=flow.priority,
            arrivalOrder=flow.arrivalOrder,
            serviceOrder=current_service_order,
            packetsRequested=flow.packetCount,
            packetsServed=served,
            packetsRemaining=remaining,
            completed=(remaining == 0),
            arrivalTime=arrival_time,
            serviceStartTime=service_start_time,
            completionTime=completion_time
        ))
        
    return ScheduleStrategyResult(
        serviceOrder=service_order,
        results=results
    )

def simulate_fifo(flows: list[FlowForScheduling], service_capacity: int) -> ScheduleStrategyResult:
    # FIFO preserves arrival order strictly
    sorted_flows = sorted(flows, key=lambda f: f.arrivalOrder)
    return _run_simulation(sorted_flows, service_capacity)

def simulate_priority(flows: list[FlowForScheduling], service_capacity: int) -> ScheduleStrategyResult:
    # Priority sorts by Priority (Desc), then Arrival Order (Asc)
    sorted_flows = sorted(
        flows, 
        key=lambda f: (-PRIORITY_WEIGHTS.get(f.priority, 0), f.arrivalOrder)
    )
    return _run_simulation(sorted_flows, service_capacity)
