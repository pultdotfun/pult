import logging
import sys
from datetime import datetime
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/pult_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("pult")

def log_error(e: Exception, context: str = ""):
    """Log error with context"""
    logger.error(f"{context} - {str(e)}", exc_info=True)

def log_info(message: str):
    """Log info message"""
    logger.info(message) 