"""
Configuration management for the Facilities Management AI Agent.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # API Keys and Authentication
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_genai_use_vertexai: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    google_cloud_project: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Application settings
    app_name: str = "Facilities Management AI Agent"
    debug: bool = os.getenv("DEBUG", "FALSE").upper() == "TRUE"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Model configuration - Both models now support Live API for voice streaming
    primary_model: str = os.getenv("PRIMARY_MODEL", "gemini-2.0-flash-live-001")
    emergency_model: str = os.getenv("EMERGENCY_MODEL", "gemini-2.0-flash-live-001")  # Changed to Live API model
    
    # File paths
    base_dir: Path = Path(__file__).parent
    data_dir: Path = base_dir / "data"
    static_dir: Path = base_dir / "static"
    templates_dir: Path = static_dir / "templates"
    
    # Business configuration
    company_name: str = os.getenv("COMPANY_NAME", "Premium Facilities Management LLC")
    emergency_keywords: list[str] = [
        "emergency", "urgent", "leak", "fire", "flood", "gas", "electrical", 
        "water", "burst", "overflow", "dangerous", "safety", "help"
    ]
    
    # Calendar settings
    calendar_id: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    default_appointment_duration: int = 120  # minutes
    
    # WebSocket settings
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 10
    
    # Audio streaming settings for ADK Live API
    audio_input_sample_rate: int = 16000   # 16kHz for input (microphone)
    audio_output_sample_rate: int = 24000  # 24kHz for output (speakers)
    audio_channels: int = 1  # Mono audio
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def validate_config() -> bool:
    """Validate required configuration settings."""
    required_fields = ["google_api_key"]
    
    for field in required_fields:
        if not getattr(settings, field):
            raise ValueError(f"Required configuration field '{field}' is missing")
    
    # Ensure data directory exists
    settings.data_dir.mkdir(exist_ok=True)
    
    # Validate Live API models
    live_models = ["gemini-2.0-flash-live-001", "gemini-2.0-flash-exp"]
    if settings.primary_model not in live_models:
        print(f"⚠️ Warning: Primary model '{settings.primary_model}' may not support Live API voice streaming")
    
    return True

# Validate configuration on import
validate_config()
