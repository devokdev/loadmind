# LoadMind — Autonomous AI DevOps & Self-Healing Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Grafana](https://img.shields.io/badge/Grafana-10.0-F46800.svg?logo=grafana&logoColor=white)](https://grafana.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-E6522C.svg?logo=prometheus&logoColor=white)](https://prometheus.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Memory-purple.svg)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/Groq-LLM_Inference-F05A28.svg)](https://groq.com/)

> **Autonomous API Stress Testing, Real-Time Observability, LLM Root-Cause Diagnostics, Automated Code Patching, and Vector Memory.**

---

## 🚀 Overview

**LoadMind** is an end-to-end Autonomous AI DevOps platform that bridges the gap between load testing, observability, and self-healing resilience engineering.

Traditional load testing tools (JMeter, k6, Locust) generate traffic but stop at raw numbers. **LoadMind autonomously closes the feedback loop**:
1. **Simulate**: Executes intelligent step-ramp synthetic user concurrency workloads.
2. **Observe**: Scrapes sub-second latency quantiles (P50, P95, P99), throughput (RPS), and Prometheus telemetry.
3. **Detect**: Automatically pinpoints the exact **Breaking Point** where SLOs are breached ($P95 > 1000\text{ms}$ or $\text{Error Rate} > 5\%$).
4. **Diagnose & Remediate**: Uses Groq LLM agents (`llama-3.3-70b-versatile`) + ChromaDB Vector Memory to analyze metrics snapshots and prescribe hot-patch code diffs.
5. **Verify & Learn**: Hot-reloads the target container, executes post-fix verification under breaking concurrency, and stores the incident signature into vector memory for sub-millisecond historical recall.

---

## 🌟 Key Features

- **Integrated Grafana Observability**: Embedded real-time Grafana dashboard suite and high-resolution dual-axis latency & concurrency curves.
- **Microsecond Step-Ramp Engine**: Progressive 5-stage concurrency ramps (e.g. 2 ➔ 4 ➔ 8 ➔ 12 ➔ 15 users) with automatic short-circuiting upon breaking point detection.
- **Groq LLM AI Diagnostician**: Multi-model fallback (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) with rich telemetry contextualization to produce natural, non-templated technical diagnoses.
- **Autonomous Remediation & Docker Hot-Reloading**: Automatically applies code diffs, rebuilds/restarts containers via the Docker SDK, and runs automated verification benchmarks.
- **Hybrid AI Memory & Vector Self-Learning**: 384-dimensional dense vector embeddings (`all-MiniLM-L6-v2`) in ChromaDB combined with relational pattern storage in PostgreSQL.
- **Minimalist Matte Dark Dashboard**: Zero-glare matte grey-black UI (`#08090d` / `#12141c`) featuring dynamic morphing CTAs (`Run Stress Test` ➔ `Apply Patch` ➔ `Run Verification` ➔ `Run Next Loop`).
- **Clean Factory Reset**: One-click **`🗑️ Clear History`** utility to flush ChromaDB vector collections, reset test runs, and restore clean sample targets before live demonstrations.

---

## 🏛️ System Architecture

```
                                ┌────────────────────────────────────────────────────────┐
                                │                 LOADMIND FRONTEND                      │
                                │      React / Tailwind / Minimalist Matte UI            │
                                │                    (Port 8080)                         │
                                └───────────────────────────┬────────────────────────────┘
                                                            │ HTTP / SSE Stream
                                                            ▼
                                ┌────────────────────────────────────────────────────────┐
                                │             FASTAPI ORCHESTRATION BACKEND              │
                                │                    (Port 8001)                         │
                                └──────┬────────────────────┬────────────────────┬───────┘
                                       │                    │                    │
              ┌────────────────────────┘                    │                    └────────────────────────┐
              ▼                                             ▼                                             ▼
┌───────────────────────────┐                 ┌───────────────────────────┐                 ┌───────────────────────────┐
│  Synthetic Worker Swarm   │                 │   Groq AI Diagnostician   │                 │  Hybrid AI Vector Memory  │
│  (httpx async coroutines) │                 │   (LLaMA 3.3 70B Engine)  │                 │  (ChromaDB + PostgreSQL)  │
└─────────────┬─────────────┘                 └───────────────────────────┘                 └───────────────────────────┘
              │
              ▼
┌───────────────────────────┐                 ┌─────────────────────────────────────────────────────────────────────────┐
│    TARGET MICROSERVICE    │◄────────────────┤                           OBSERVABILITY SUITE                           │
│  FastAPI + SQLAlchemy DB  │  Scrapes        │   Prometheus (:9090)  +  Grafana Embedded Dashboard (:3000)             │
│        (Port 8002)        │  Metrics        └─────────────────────────────────────────────────────────────────────────┘
└───────────────────────────┘
```

---

## 🔬 Built-in Failure Scenarios & Patches

| Scenario | Route | Simulated Bottleneck | Autonomous Remediation |
| :--- | :--- | :--- | :--- |
| **E-Commerce Checkout** | `/checkout/process` | Synchronous blocking call (`time.sleep`) stalling FastAPI ASGI event loop | Rewrites route to non-blocking async execution (`await asyncio.sleep`) |
| **Database N+1 Query** | `/products` | Relational query multiplication executing individual SQL queries per item inside a loop | Replaces loop with eager loading via SQLAlchemy `joinedload(Product.vendor)` |
| **Connection Pool Starvation** | `/db-status` | Long-held transactional sessions (`pg_sleep`) starving PostgreSQL connection limits | Reclaims idle sessions and scales connection pool overflow capacity |
| **Third-Party Payment Gateway** | `/payments/process` | External network latency blocking server worker thread | Wraps downstream HTTP client with async circuit breaker & timeout shield |

---

## 📊 Core Telemetry Metrics

- **P50 Latency**: Median response time across 50% of completed transactions.
- **P95 Latency**: 95th-percentile latency — the standard benchmark for **Service Level Objectives (SLOs)**.
- **P99 Latency**: Tail latency capturing worst-case delays, thread locks, and queue backups.
- **Throughput (req/s)**: Processed volume in requests per second.
- **Error Rate (%)**: Percentage of HTTP 4xx / 5xx responses out of total requests sent.
- **Breaking Point Rule**: Triggered when $P95 > 1000\text{ms}$ or $\text{Error Rate} > 5\%$.

---

## 🛠️ Quick Start

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Groq API Key](https://console.groq.com/) *(Free tier provides instantaneous inference)*

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 3. Launch the Stack
```bash
docker-compose up --build
```

### 4. Open the Platform
Navigate to:
👉 **[http://localhost:8080](http://localhost:8080)**

---

## 🌐 Port Allocation Reference

| Service | Port | Description |
| :--- | :--- | :--- |
| **Frontend UI** | `8080` | Matte Single-Pane Dark Interface |
| **Backend API** | `8001` | FastAPI Orchestration Engine |
| **Target App** | `8002` | Test microservice with dynamic failure simulator |
| **Grafana** | `3000` | Embedded Observability Suite (`admin` / `admin`) |
| **Prometheus** | `9090` | Time-Series Telemetry Database |
| **ChromaDB** | `8003` | Dense Vector Knowledge Memory Store |
| **PostgreSQL** | `5434` / `5432` | Relational Storage & Incident Signatures |

---

## 🧪 3-Minute Live Demo Flow

1. **Clean Slate**: Click **`🗑️ Clear History`** to reset past vector memory and restore target baseline.
2. **Launch Stress Test**: Select **`E-Commerce Checkout Stress`** and click **`▶ Run Stress Test`**.
3. **Observe Step-Ramp Load**: Watch the Live Curves dual-axis monitor scale user concurrency (purple dashed line) while tracking real-time P95/P50 latency curves.
4. **Inspect AI Diagnosis**: Review the Groq AI diagnosis detailing why event loop starvation caused the breaking point.
5. **Apply Patch**: Click **`🔧 Apply Patch`** to hot-reload the target container via Docker.
6. **Verify Resilience**: Click **`✓ Run Verification`** to benchmark the post-fix latency drop (**98%+ latency improvement**).
7. **Inspect Incident Memory**: Switch to **`Incident Memory`** to inspect the 384-dimensional vector embeddings stored in ChromaDB for historical recall.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
