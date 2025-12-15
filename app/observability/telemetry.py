from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI
import os

def setup_telemetry(app: FastAPI):
    # Retrieve service name from env or config
    service_name = "multimodal-rag"
    
    # Configure Tracer Provider
    provider = TracerProvider()
    
    # In production, use OTLPSpanExporter to send to Jaeger/Tempo
    # publisher = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
    
    # For this setup, we use Console to verify it works without external infra
    # processor = BatchSpanProcessor(ConsoleSpanExporter())
    # provider.add_span_processor(processor)

    
    trace.set_tracer_provider(provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
