from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log Request
        logger.info(f"Incoming Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            
            # Log Response
            process_time = (time.time() - start_time) * 1000
            logger.info(f"Response: {response.status_code} | Duration: {process_time:.2f}ms")
            
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
