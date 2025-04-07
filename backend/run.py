import sys
import uvicorn
from app.core.logging_config import configure_logging

if __name__ == "__main__":
    # Configure logging before starting the application
    configure_logging()
    
    # Start uvicorn with custom log config
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=False,  # Disable uvicorn's default access log since we're handling it in our config
    ) 