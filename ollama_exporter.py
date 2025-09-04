from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY
from starlette.responses import Response
import time
import requests

app = FastAPI()

# Metrics
OLLAMA_REQUESTS = Counter("ollama_requests_total", "Total number of requests to Ollama")
OLLAMA_FAILURES = Counter("ollama_failures_total", "Failed requests to Ollama")
OLLAMA_LATENCY = Histogram("ollama_request_duration_seconds", "Request latency to Ollama")

OLLAMA_HOST = "http://ollama:11434"  # service name in docker-compose

@app.get("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.get("/probe")
def probe():
    """Test Ollama API health & measure latency"""
    start = time.time()
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if r.status_code == 200:
            OLLAMA_REQUESTS.inc()
        else:
            OLLAMA_FAILURES.inc()
    except Exception:
        OLLAMA_FAILURES.inc()
    finally:
        duration = time.time() - start
        OLLAMA_LATENCY.observe(duration)
    return {"latency": duration}

