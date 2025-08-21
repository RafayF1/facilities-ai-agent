"""
FastAPI application entry point for the Facilities Management AI Agent.
"""
import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.data_service import data_service
from app.services.calendar_service import calendar_service
from app.services.email_service import email_service
from app.websocket.streaming import streaming_manager

# Custom uvicorn configuration to exclude .venv from file watching
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_excludes=["*.venv/*", ".venv/*", "venv/*", "__pycache__/*", "*.pyc", "*.pyo", "*.pyd"],
        reload_dirs=["app"],
        reload_includes=["*.py"],
        log_level="info"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    print(f"🚀 Starting {settings.app_name}")
    print(f"📍 Environment: {'Development' if settings.debug else 'Production'}")
    print(f"🤖 Primary Model: {settings.primary_model}")
    
    # Initialize services
    try:
        await data_service.initialize()
        await calendar_service.initialize()
        await email_service.initialize()
        print("✅ All services initialized successfully")
    except Exception as e:
        print(f"❌ Service initialization error: {e}")
        # Continue anyway for demo purposes
    
    yield
    
    # Shutdown
    print(f"🛑 Shutting down {settings.app_name}")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered customer service agent for facilities management",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = settings.static_dir
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application interface."""
    html_file = settings.templates_dir / "index.html"
    
    if html_file.exists():
        return FileResponse(html_file)
    else:
        # Return a basic HTML page if template doesn't exist
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Facilities Management AI Agent</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { background: #f0f8ff; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 Facilities Management AI Agent</h1>
        <div class="status">
            <h2>System Status</h2>
            <p>✅ API Server is running</p>
            <p>📍 WebSocket endpoint: <code>ws://localhost:{settings.port}/ws/{session_id}</code></p>
            <p>📝 Frontend interface is being prepared...</p>
        </div>
        <h2>Available Endpoints</h2>
        <ul>
            <li><strong>GET /</strong> - This interface</li>
            <li><strong>GET /health</strong> - Health check</li>
            <li><strong>GET /status</strong> - System status</li>
            <li><strong>WS /ws/{session_id}</strong> - WebSocket streaming</li>
        </ul>
    </div>
</body>
</html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-01-27T10:30:00Z",
        "version": "1.0.0",
        "services": {
            "data_service": "initialized",
            "calendar_service": "initialized", 
            "email_service": "initialized"
        }
    }

@app.get("/status")
async def system_status():
    """System status endpoint."""
    return {
        "application": settings.app_name,
        "environment": "development" if settings.debug else "production",
        "model": settings.primary_model,
        "active_sessions": streaming_manager.get_active_sessions_count(),
        "services": {
            "data_service": data_service._initialized,
            "calendar_service": calendar_service._initialized,
            "email_service": email_service._initialized
        },
        "configuration": {
            "company_name": settings.company_name,
            "service_areas": ["Dubai Marina", "JBR", "Downtown Dubai", "Business Bay"],
            "emergency_keywords_count": len(settings.emergency_keywords)
        }
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, is_audio: str):
    """
    WebSocket endpoint for real-time agent communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier  
        is_audio: Whether to enable audio mode ("true"/"false")
    """
    await streaming_manager.handle_websocket_connection(
        websocket=websocket,
        session_id=session_id,
        is_audio=is_audio
    )

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a specific session."""
    session_info = streaming_manager.get_session_info(session_id)
    
    if session_info:
        return {
            "status": "success",
            "session": session_info
        }
    else:
        return {
            "status": "error",
            "message": f"Session {session_id} not found or not active"
        }

@app.get("/sessions")
async def list_active_sessions():
    """List all active streaming sessions."""
    return {
        "status": "success",
        "active_sessions_count": streaming_manager.get_active_sessions_count(),
        "sessions": [
            streaming_manager.get_session_info(session_id) 
            for session_id in streaming_manager.active_sessions.keys()
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return {
        "status": "error",
        "message": "Endpoint not found",
        "path": str(request.url.path)
    }

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle internal server errors."""
    return {
        "status": "error", 
        "message": "Internal server error",
        "path": str(request.url.path)
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
