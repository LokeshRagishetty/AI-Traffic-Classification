from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.traffic import (
    TrafficGenerateRequest, TrafficGenerateResponse,
    TrafficClassifyRequest, TrafficClassifyResponse,
    MLMetricsResponse,
    ScheduleSimulateRequest, ScheduleSimulateResponse,
    MetricsCompareResponse
)
from services.traffic_generator import generate_synthetic_traffic
from services.traffic_classifier import classifier
from services.scheduler_service import simulate_fifo, simulate_priority

app = FastAPI(title="AI Network Traffic Classification API")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Train the model during backend initialization
    classifier.train(num_flows=5000)

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "AI Network Traffic Classification API"
    }

@app.post("/api/traffic/generate", response_model=TrafficGenerateResponse)
def generate_traffic(request: TrafficGenerateRequest):
    flows = generate_synthetic_traffic(count=request.count, seed=request.seed)
    return TrafficGenerateResponse(flows=flows, count=len(flows))

@app.get("/api/ml/metrics", response_model=MLMetricsResponse)
def get_ml_metrics():
    metrics = classifier.get_metrics()
    return MLMetricsResponse(**metrics)

@app.post("/api/classify", response_model=TrafficClassifyResponse)
def classify_traffic(request: TrafficClassifyRequest):
    results = classifier.predict(request.flows)
    return TrafficClassifyResponse(results=results)

@app.post("/api/schedule/simulate", response_model=ScheduleSimulateResponse)
def simulate_schedule(request: ScheduleSimulateRequest):
    if not request.flows:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Flows list cannot be empty")
        
    fifo_result = simulate_fifo(request.flows, request.serviceCapacity)
    priority_result = simulate_priority(request.flows, request.serviceCapacity)
    
    return ScheduleSimulateResponse(
        fifo=fifo_result,
        priority=priority_result
    )

@app.post("/api/metrics/compare", response_model=MetricsCompareResponse)
def compare_metrics(request: ScheduleSimulateRequest):
    if not request.flows:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Flows list cannot be empty")
        
    # 1. Run simulation to get exact deterministic scheduling
    fifo_result = simulate_fifo(request.flows, request.serviceCapacity)
    priority_result = simulate_priority(request.flows, request.serviceCapacity)
    
    # Map for O(1) lookup of original flows
    original_flows_map = {f.flowId: f for f in request.flows}
    
    # 3. Determine common simulation horizon for fairness
    fifo_max_completion = max([r.completionTime for r in fifo_result.results] + [0.0])
    priority_max_completion = max([r.completionTime for r in priority_result.results] + [0.0])
    common_horizon = max(fifo_max_completion, priority_max_completion)
    
    # 4. Calculate metrics
    from services.metrics_service import calculate_metrics
    fifo_metrics = calculate_metrics(fifo_result, original_flows_map, common_horizon)
    priority_metrics = calculate_metrics(priority_result, original_flows_map, common_horizon)
    
    return MetricsCompareResponse(
        fifo=fifo_metrics,
        priority=priority_metrics,
        fifoSchedule=fifo_result,
        prioritySchedule=priority_result
    )
