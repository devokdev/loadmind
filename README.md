# LoadMind — Autonomous API Stress Testing & Self-Learning Platform

**LoadMind** is a universal API stress testing and autonomous resilience engineering platform. It allows any engineering team or external microservice to simulate realistic synthetic traffic swarms, automatically pinpoint performance breaking points, diagnose the underlying root causes using Groq LLMs, generate remediation code diffs, and continuously memorize failure signatures into vector + relational memory.

---

## Key Features

- **Universal API Compatibility**: Stress-test any local or external REST endpoint (`GET`, `POST`, `PUT`, `DELETE`) with custom headers, query parameters, and payload templates.
- **Simulated Persona Swarms**: Choose from built-in virtual user personas (*Standard Consumer*, *E-Commerce Shopper*, *Heavy Read Query*, *Spiky Aggressive Burst*).
- **Flexible Load Profiles**: Execute *Step Ramp-Up*, *Sudden Traffic Spikes*, or *Constant Sustained Load*.
- **Real-Time Telemetry Curve**: Live tracking of P50, P90, P95, and P99 latency percentiles, throughput (RPS), error rates, and HTTP status code distributions.
- **Autonomous Root Cause Diagnosis (Powered by Groq)**: Automatically isolates bottlenecks such as:
  - `blocking_async` / synchronous wait times
  - `n_plus_one` database queries
  - `db_pool` connection saturation
  - `server_concurrency_exhaustion`
  - `rate_limit_throttle`
  - `unbounded_cache` memory growth
  - `missing_index` on DB queries
- **Self-Learning AI Memory Store**: Automatically indexes failure signatures, symptoms, and verified remediation strategies into **ChromaDB + PostgreSQL / SQLite** for progressive learning across runs.
- **Automated Code Diff & Architecture Remediation**: Generates instant code patches and architectural scaling guidance.
- **Minimalist Dark Matte Dashboard**: Single-pane-of-glass UI (`#0f1117` / `#161821`), zero glare, with instant one-click scenario presets.

---

## Architecture

```
                               ┌─────────────────────────────┐
                               │  Minimalist Matte Dashboard │
                               │      (Port 8080 - Nginx)    │
                               └──────────────┬──────────────┘
                                              │ HTTP / SSE
                                              ▼
                               ┌─────────────────────────────┐
                               │   FastAPI Backend Core      │
                               │      (Port 8001)            │
                               └──────┬───────┬───────┬──────┘
                                      │       │       │
              ┌───────────────────────┘       │       └─────────────────────────┐
              ▼                               ▼                                 ▼
┌───────────────────────────┐   ┌───────────────────────────┐     ┌───────────────────────────┐
│ Async Synthetic Swarm /   │   │ Groq AI Diagnostic Core   │     │ Hybrid AI Memory Store    │
│ Locust Engine (Port 8089) │   │ (groq/compound-mini)      │     │ (ChromaDB + PostgreSQL)   │
└─────────────┬─────────────┘   └───────────────────────────┘     └───────────────────────────┘
              │
              ▼
┌───────────────────────────┐
│ Target API / Microservice │
│ (e.g. Port 8002 / Remote) │
└───────────────────────────┘
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Groq API Key](https://console.groq.com/) *(Free, ultra-fast inference)*

---

## Quick Start Guide

### 1. Set Up Environment
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=groq/compound-mini
```

### 2. Start the Application Stack
```bash
docker-compose up --build
```

### 3. Open the Matte Dashboard
Open your browser and navigate to:
👉 **[http://localhost:8080](http://localhost:8080)**

---

## 3-Minute Demonstration Walkthrough

1. **Launch a Demo Scenario**:
   - In the top-left card under **"One-Click Demo Scenarios"**, click **`E-Commerce Checkout Stress`** (or **`Database Heavy /products`**).
   - Click **`Launch Stress Test & AI Learner`**.
2. **Observe Live Telemetry**:
   - Watch the live graph plot latency curve (P95), throughput (req/s), and virtual user ramp-up.
3. **Inspect AI Diagnosis**:
   - Once the test finishes, the **Autonomous Diagnostician** identifies the exact breaking point and failure mode.
4. **Apply Remediation Patch**:
   - View the generated code patch diff and architectural scaling advice.
   - Click **`Apply Remediation Patch`** to update the codebase and verify the resilience gain.
5. **Explore AI Memory**:
   - Click the **`AI Memory`** tab in the top navigation bar to inspect the stored bottleneck signatures and learned remedies.

---

## Port Allocation Reference

| Service | Port | Description |
| :--- | :--- | :--- |
| **Frontend Dashboard** | `8080` | Matte Single-Pane UI |
| **Backend API** | `8001` | FastAPI Stress & AI Engine |
| **Target App** | `8002` | Sample API with failure simulator |
| **Locust Swarm** | `8089` | Distributed load generator |
| **Prometheus** | `9090` | System & container metrics |
| **cAdvisor** | `8085` | Container metrics aggregator |
| **ChromaDB** | `8003` | Vector database for memory |
| **PostgreSQL** | `5434` / `5432` | Relational storage & patterns |

---

## Stopping the Stack

```bash
docker-compose down
```
To clear persisted database volumes:
```bash
docker-compose down -v
```

