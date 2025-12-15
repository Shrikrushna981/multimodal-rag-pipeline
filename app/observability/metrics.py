from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

# Metrics Definitions
REQUEST_COUNT = Counter(
    "app_request_count", 
    "Total request count", 
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds", 
    "Request latency", 
    ["method", "endpoint"]
)

LLM_TOKEN_USAGE = Counter(
    "app_llm_token_usage",
    "Token usage by LLM",
    ["model", "type"] # type: prompt, completion
)

LLM_LATENCY = Histogram(
    "app_llm_latency_seconds",
    "LLM generation latency",
    ["model"]
)

INGESTION_COUNT = Counter(
    "app_ingestion_count",
    "Number of files ingested",
    ["mime_type", "status"]
)

# Endpoint to scrape
router = APIRouter()

@router.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
