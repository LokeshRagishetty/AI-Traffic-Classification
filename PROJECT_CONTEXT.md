# Project Context: AI-Based Network Traffic Classification

## Project Objective
The objective of this project is to demonstrate a conceptual pipeline for AI-based network traffic classification to improve packet transmission performance.

## MVP Scope
This is ONLY an MVP DEMO / SIMULATION.
It does NOT implement real packet forwarding, kernel networking, router configuration, SDN, real-time traffic interception, or production network optimization.

## Architecture
- **Frontend**: React + Vite application serving as the dashboard for simulation.
- **Backend**: Python + FastAPI application handling API requests, generating synthetic traffic, classifying traffic via scikit-learn, prioritizing, scheduling, and calculating metrics.
- **Communication**: REST API between frontend and backend.
- **Data**: Synthetic traffic generated locally by the backend. No database is required for the MVP.

## Technology Stack
- Frontend: React, Vite, Tailwind CSS, Recharts
- Backend: Python, FastAPI, Uvicorn, Pydantic, Numpy, Pandas
- ML: scikit-learn

## Current Phase: Phase 7 — Final Dashboard & Demo Polish
- **Status**: COMPLETED / FROZEN.

## Final Dashboard Workflow
1. **Synthetic Traffic Generation**: Controls for injecting simulated flows with accurate protocol metadata.
2. **AI Traffic Classification**: Applies `RandomForestClassifier` and visualizes predicted types and accuracies.
3. **Priority Distribution**: Evaluates rigid deterministic QoS mappings (Gaming -> Critical, Web -> Medium).
4. **Scheduling Simulation**: Passes unified payloads through strict bottleneck evaluations, differentiating chronological FIFO handling vs Priority handling.
5. **Performance Comparison**: Validates metrics generated cleanly on an identical simulation horizon preventing bias.
6. **Simulation Insights**: Highlights context-aware takeaways directly from metrics calculations automatically.
7. **Methodology & Limitations**: A detailed architectural breakdown reinforcing the simulation's mathematical isolation from real OSI layer networks.

## Performance Metrics Model
- **Simulation Time Unit**: 0.05 seconds between Flow Arrivals. 0.001 seconds per single packet processing execution.
- **Average Queue Latency**: `sum(max(0, serviceStartTime - arrivalTime)) / n`
- **Max Queue Latency**: `max(max(0, serviceStartTime - arrivalTime))`
- **Throughput**: `(Total Bytes Served Within Simulation Horizon * 8) / commonSimulationDuration (converted to Mbps)`.
- **Packet Loss**: `(packetsRemaining / packetsRequested) * 100`.
- **Jitter**: `sum(abs(delay[i] - delay[i-1])) / (n-1)` for n >= 2, otherwise 0.

## Important Constraint
This project is an academic simulation and demonstration. It uses **synthetic data** to illustrate the concept of AI-based QoS (Quality of Service). It is not designed or intended to manipulate real network packets or interface with physical network interfaces.
