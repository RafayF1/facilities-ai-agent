#!/usr/bin/env python3
"""
Simple script to run the Facilities Management AI Agent without reload.
Use this for stable testing without file watching issues.
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("🚀 Starting Facilities Management AI Agent (No Reload Mode)")
    print(f"📍 Environment: {'Development' if settings.debug else 'Production'}")
    print(f"🤖 Primary Model: {settings.primary_model}")
    print("📝 Use this mode for stable testing without file watching issues")
    print("🔄 To enable reload mode, use: uv run python -m app.main")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Disable reload for stable testing
        log_level="info"
    ) 