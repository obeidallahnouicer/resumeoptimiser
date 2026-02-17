"""Application entry point."""

import uvicorn
from dotenv import load_dotenv
from src.main import app
from src.core.config import SERVER_HOST, SERVER_PORT, DEBUG


# Load environment variables from .env file
load_dotenv()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG,
        log_level="info"
    )