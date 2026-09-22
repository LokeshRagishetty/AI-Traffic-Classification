from pydantic import BaseModel, Field
from typing import List, Optional

class TrafficFlow(BaseModel):
    flowId: str
    timestamp: str
    protocol: str
    sourcePort: int
    destinationPort: int
    packetCount: int
    averagePacketSize: float
    packetsPerSecond: float
    bytesPerSecond: float
    flowDuration: float
    averageInterArrivalTime: float
    tcpFlagPattern: str
    groundTruthClass: str

class TrafficGenerateRequest(BaseModel):
    count: int = Field(100, ge=1, le=1000)
    seed: Optional[int] = None

class TrafficGenerateResponse(BaseModel):
    flows: List[TrafficFlow]
    count: int

class TrafficClassifyRequest(BaseModel):
    flows: List[TrafficFlow]

class TrafficClassificationResult(BaseModel):
    flowId: str
    predictedClass: str
    confidence: float
    priority: str

class TrafficClassifyResponse(BaseModel):
    results: List[TrafficClassificationResult]

class MLMetricsResponse(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    classes: List[str]
    confusionMatrix: List[List[int]]

class FlowForScheduling(BaseModel):
    flowId: str
    trafficClass: str # This should be the predictedClass
    priority: str
    packetCount: int
    averagePacketSize: float
    arrivalOrder: int # original index

class ScheduleSimulateRequest(BaseModel):
    flows: List[FlowForScheduling]
    serviceCapacity: int = Field(100, gt=0)

class ScheduledFlowResult(BaseModel):
    flowId: str
    trafficClass: str
    priority: str
    arrivalOrder: int
    serviceOrder: int
    packetsRequested: int
    packetsServed: int
    packetsRemaining: int
    completed: bool
    arrivalTime: float
    serviceStartTime: float
    completionTime: float

class ScheduleStrategyResult(BaseModel):
    serviceOrder: List[str] # List of flowIds in the exact order they were serviced
    results: List[ScheduledFlowResult]

class ScheduleSimulateResponse(BaseModel):
    fifo: ScheduleStrategyResult
    priority: ScheduleStrategyResult

class PerformanceMetrics(BaseModel):
    averageQueueLatency: float
    maxQueueLatency: float
    throughputMbps: float
    packetLossPercentage: float
    jitter: float

class MetricsCompareResponse(BaseModel):
    fifo: PerformanceMetrics
    priority: PerformanceMetrics
    fifoSchedule: ScheduleStrategyResult
    prioritySchedule: ScheduleStrategyResult
