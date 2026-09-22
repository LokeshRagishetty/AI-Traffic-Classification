# AI-Based Network Traffic Classification
### Improving Packet Transmission Performance via Machine Learning

> **Academic Simulation Only** — This project is an MVP prototype using synthetic traffic and simulated packet scheduling. It does not capture, transmit, or modify real network packets. All results are simulation outputs and should not be interpreted as real-world network benchmarks.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Pipeline](#pipeline)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [How to Run](#how-to-run)
7. [Demo Workflow](#demo-workflow)
8. [API Reference](#api-reference)
9. [Performance Metrics](#performance-metrics)
10. [Limitations](#limitations)

---

## Project Overview

This project demonstrates a conceptual AI-based pipeline for classifying network traffic and simulating packet scheduling priority. The goal is to show how machine learning can identify traffic types (e.g., Gaming, Video Streaming, VoIP) and how deterministic priority-based scheduling can theoretically improve Quality of Service (QoS) compared to simple FIFO scheduling.

**Key Concepts Demonstrated:**
- Synthetic generation of realistic network flow data
- Machine learning classification of network traffic types
- Deterministic QoS priority assignment based on traffic class
- Simulated FIFO vs AI-Priority packet scheduling comparison
- Performance metric analysis (latency, throughput, packet loss, jitter)

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                  Frontend Dashboard                        │
│              React + Vite + Tailwind CSS                   │
│                   localhost:5173                           │
│                                                           │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Generate │  │  Classify   │  │  Simulate & Compare  │  │
│  │ Traffic  │→ │  AI Model   │→ │  FIFO vs AI-Priority │  │
│  └──────────┘  └─────────────┘  └──────────────────────┘  │
└─────────────────────────┬─────────────────────────────────┘
                          │ REST API (JSON)
                          ▼
┌───────────────────────────────────────────────────────────┐
│                  Backend API Server                        │
│             Python FastAPI + Uvicorn                       │
│                  localhost:8000                            │
│                                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Traffic Generator → Classifier → Priority Service    │  │
│  │        → Scheduler Service → Metrics Service         │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## Pipeline

```
STEP 1: Synthetic Traffic Generation
         ↓
   Generates N synthetic network flows with realistic
   attributes (packet count, size, protocol, rate)
   for 5 traffic classes.
         ↓

STEP 2: AI Classification (Random Forest)
         ↓
   RandomForestClassifier predicts the traffic type
   of each flow based on its numeric features.
   Returns: Predicted Class + Confidence Score
         ↓

STEP 3: Deterministic Priority Assignment
         ↓
   Hard-coded QoS rules map class → priority:
   Gaming / VoIP       → Critical
   Video Streaming     → High
   Web Browsing        → Medium
   File Transfer       → Low
         ↓

STEP 4: Scheduling Simulation (Software-only)
         ↓
   Same workload evaluated under two algorithms:
   ┌─────────────────┐     ┌─────────────────────┐
   │ FIFO Scheduling │     │ AI-Priority Sched.  │
   │ Arrival order   │     │ Critical > High >   │
   │ is preserved    │     │ Medium > Low        │
   └─────────────────┘     └─────────────────────┘
         ↓

STEP 5: Performance Metrics Comparison
   (Common simulation horizon applied to both)
         ↓
   Average Queue Latency | Max Queue Latency
   Throughput (Mbps)     | Packet Loss (%)
   Jitter (s)
         ↓

STEP 6: Simulation Insights
   Objective, data-driven observations derived
   from actual API results.
```

---

## Tech Stack

| Layer     | Technology            | Purpose                                           |
|-----------|-----------------------|---------------------------------------------------|
| Frontend  | React 18 + Vite       | SPA framework and build tool                      |
| Frontend  | Tailwind CSS          | Utility-first styling                             |
| Frontend  | Recharts              | Bar and Pie chart visualizations                  |
| Frontend  | Lucide React          | Icon library                                      |
| Backend   | Python 3.9+           | Core language                                     |
| Backend   | FastAPI               | REST API framework                                |
| Backend   | Uvicorn               | ASGI server                                       |
| Backend   | Pydantic              | Request/response schema validation                |
| Backend   | NumPy + Pandas        | Numeric computation for traffic generation        |
| ML        | scikit-learn          | RandomForestClassifier pipeline                   |

---

## Project Structure

```
CN_Project/
├── backend/
│   ├── main.py                      # FastAPI app and route definitions
│   ├── requirements.txt             # Python dependencies
│   ├── models/
│   │   └── traffic.py               # Pydantic schemas (request/response models)
│   ├── services/
│   │   ├── traffic_generator.py     # Synthetic flow generation
│   │   ├── traffic_classifier.py   # Random Forest ML pipeline
│   │   ├── priority_service.py      # Deterministic priority mapping
│   │   ├── scheduler_service.py     # FIFO and AI-Priority simulation
│   │   └── metrics_service.py       # Latency, throughput, jitter calculations
│   └── tests/
│       ├── test_traffic.py          # Generator tests
│       ├── test_classifier.py       # ML model tests
│       ├── test_priority.py         # Priority mapping tests
│       ├── test_scheduler.py        # Scheduler algorithm tests
│       └── test_metrics.py          # Metric calculation tests
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main dashboard component (7-step flow)
│   │   └── index.css                # Global Tailwind CSS import
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── PROJECT_CONTEXT.md               # Internal technical reference
└── README.md                        # This file
```

---

## How to Run

### Prerequisites
- **Python 3.9+** with `pip`
- **Node.js 18+** with `npm`

---

### Step 1: Start the Backend Server

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (first time only)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Install Python dependencies (first time only)
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload
```

The backend API will be available at: **`http://127.0.0.1:8000`**

You can inspect the auto-generated API docs at: **`http://127.0.0.1:8000/docs`**

---

### Step 2: Start the Frontend Dashboard

Open a **new terminal window** and run:

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The dashboard will be available at: **`http://localhost:5173`**

---

### Step 3: Run Backend Tests

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/
```

Expected output: **31 passed**

---

## Demo Workflow

Once both servers are running, open `http://localhost:5173` in your browser and follow the 6-step workflow on the dashboard:

| Step | Action | What Happens |
|------|--------|--------------|
| 1 | Set flow count → Click **Generate Traffic** | Backend synthesizes `N` network flows with randomized attributes across 5 traffic classes |
| 2 | Click **Classify Workload** | RandomForest model predicts each flow's type and confidence score |
| 3 | Review **Priority Distribution** | Deterministic mapping assigns Critical/High/Medium/Low to each flow |
| 4 | Set bottleneck capacity → Click **Run Simulation** | Both FIFO and AI-Priority algorithms process the identical workload |
| 5 | Review **Performance Comparison** | Latency, Throughput, Packet Loss, and Jitter are displayed side-by-side |
| 6 | Read **Simulation Insights** | Context-aware observations automatically derived from the API results |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check — confirms API is running |
| `POST` | `/api/traffic/generate` | Generate synthetic network flows |
| `POST` | `/api/classify` | Run AI classification on generated flows |
| `GET` | `/api/ml/metrics` | Retrieve model accuracy, F1 score, confusion matrix |
| `POST` | `/api/schedule/simulate` | Run raw FIFO vs AI-Priority scheduling simulation |
| `POST` | `/api/metrics/compare` | Run simulation and return full performance metrics |

---

## Performance Metrics

All metrics are calculated from the simulation output over a **common simulation horizon** (the maximum completion time across both strategies) to ensure a fair, unbiased comparison.

| Metric | Formula |
|--------|---------|
| **Average Queue Latency** | `sum(max(0, serviceStartTime − arrivalTime)) / completedFlows` |
| **Maximum Queue Latency** | `max(max(0, serviceStartTime − arrivalTime))` |
| **Throughput (Mbps)** | `(totalBytesServed × 8) / commonSimulationDuration / 1,000,000` |
| **Packet Loss (%)** | `(packetsRemaining / packetsRequested) × 100` |
| **Jitter (s)** | `sum(|delay[i] − delay[i−1]|) / (n − 1)` for n ≥ 2, else `0` |

**Simulation Time Model:**
- `arrivalTime = arrivalOrder × 0.05` (50ms between flow arrivals)
- `processingTime = packetCount × 0.001` (1ms per packet)

---

## Limitations

- **No real networking** — This system operates entirely in application memory. No sockets, no kernel interfaces, no packet capture.
- **Synthetic data only** — Flow features are generated programmatically within fixed bounds to exhibit class-specific patterns.
- **Simplified latency model** — "Queue Latency" reflects only buffer wait time. Real-world latency also includes propagation delay, serialization delay, and router queuing.
- **No congestion modelling** — Throughput does not account for TCP slow-start, congestion windows, or retransmission.
- **No persistence** — No database. All simulation state exists only in memory during a session.
# AI-Traffic-Classification
