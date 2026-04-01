from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.api.routes import upload, analyze, results, health
# from app.core.exceptions import register_exception_handlers

# Phase 3 routers
from app.auth.routes import router as auth_router
from app.community.routes.posts import router as posts_router
from app.community.routes.comments import router as comments_router
from app.community.routes.reactions import router as reactions_router
from app.api.routes.leaderboard import router as leaderboard_router
from app.api.routes.insights import router as insights_router

# Phase 4 routers
from app.api.routes.admin import router as admin_router
from app.api.routes.stream import router as stream_router
from app.api.routes.provenance import router as provenance_router
from app.api.routes.social import router as social_router
from app.extension.extension_routes import router as extension_router

app = FastAPI(title="TruthLens API", version="4.0.0")


# ─── Extension CORS Middleware ────────────────────────────────────────────────
# Browser extensions send requests from chrome-extension:// or moz-extension://
# FastAPI CORSMiddleware does not support dynamic wildcard matching for these,
# so we use a custom middleware that checks origin prefix.

class ExtensionCORSMiddleware(BaseHTTPMiddleware):
    EXTENSION_PREFIXES = ("chrome-extension://", "moz-extension://")

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")

        # Handle preflight OPTIONS for extension origins
        if request.method == "OPTIONS" and origin.startswith(self.EXTENSION_PREFIXES):
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                },
            )

        response = await call_next(request)

        # Attach CORS headers for extension origins
        if origin.startswith(self.EXTENSION_PREFIXES):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


# Extension CORS must be added BEFORE the standard CORSMiddleware
app.add_middleware(ExtensionCORSMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       # Next.js dev
        "https://truthlens.app",       # production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Rate Limiter (slowapi) ──────────────────────────────────────────────────
try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from app.extension.extension_routes import limiter

    if limiter:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except ImportError:
    pass  # slowapi not installed — rate limiting disabled

# Phase 2 routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")

# Phase 3 routers
app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(reactions_router)
app.include_router(leaderboard_router)
app.include_router(insights_router)

# Phase 4 routers
app.include_router(admin_router)
app.include_router(stream_router)
app.include_router(provenance_router)
app.include_router(social_router)
app.include_router(extension_router)

# register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    # Preload quick-scan models (EfficientNetV2 + CLIP) into web worker memory.
    # These models run in-process for <3s latency — NOT dispatched to Celery.
    from app.extension.extension_routes import _preload_models
    _preload_models()

    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA/ROCm is available. Detecting GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA/ROCm is not available. Running on CPU.")
    except ImportError:
        print("Torch is not installed. Skipping GPU check.")
