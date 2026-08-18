# LoadMind

LoadMind is a comprehensive, intelligent load testing and monitoring platform. It integrates load generation, metrics collection, and AI-powered insights to help you understand your application's performance characteristics under stress.

## Architecture

The platform consists of several core components deployed via Docker Compose:

- **Frontend**: Web interface for managing tests and viewing results (available on port `8080`).
- **Backend**: Python-based API service orchestrating load tests, data collection, and AI interactions (available on port `8001`).
- **Locust**: Distributed user load testing tool (available on port `8089`).
- **Prometheus**: Time-series database for collecting metrics from the target app and infrastructure (available on port `9090`).
- **cAdvisor**: Analyzes resource usage and performance characteristics of running containers.
- **Postgres**: Relational database for storing test configurations and metadata.
- **ChromaDB**: Vector database for AI-driven insights and retrieval.
- **Target App**: The sample application being tested.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Gemini API Key (for AI-powered insights)

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd LoadMind
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory (or export the variable) with your Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Start the application**:
   Use Docker Compose to build and start all services:
   ```bash
   docker-compose up --build
   ```

4. **Access the services**:
   - Frontend UI: http://localhost:8080
   - Backend API: http://localhost:8001
   - Locust UI: http://localhost:8089
   - Prometheus: http://localhost:9090

## Project Structure

- `/backend`: Python backend service (FastAPI/Flask)
- `/frontend`: Web user interface
- `/locust`: Locust load testing scripts and configurations
- `/prometheus`: Prometheus configuration
- `/target-app`: The application acting as the target for load tests

## Stopping the Application

To stop the services and remove the containers, run:
```bash
docker-compose down
```

To also remove the persisted volumes (Postgres and ChromaDB data):
```bash
docker-compose down -v
```
