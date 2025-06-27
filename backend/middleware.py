import time
from typing import Dict, List
from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import logging
from config import settings

logger = logging.getLogger(__name__)

# In-memory rate limiting (use Redis in production)
rate_limit_store: Dict[str, List[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Clean old requests outside the window
        current_time = time.time()
        rate_limit_store[client_ip] = [
            req_time for req_time in rate_limit_store[client_ip]
            if current_time - req_time < self.window_size
        ]
        
        # Check if rate limit exceeded
        if len(rate_limit_store[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.requests_per_minute} per minute",
                    "retry_after": 60
                }
            )
        
        # Add current request
        rate_limit_store[client_ip].append(current_time)
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(rate_limit_store[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_size)
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Remove server information
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url} from {request.client.host}")
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} - {request.method} {request.url} "
                f"took {process_time:.3f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} - {request.method} {request.url} "
                f"took {process_time:.3f}s"
            )
            raise


def setup_middleware(app):
    """Setup all middleware for the FastAPI app"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware (in production)
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure with your domain in production
        )
    
    # Custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute) 