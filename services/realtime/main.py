import logging

from fastapi import FastAPI

# Basic setup for logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()


# Basic route
@app.get("/")
async def root():
    logger.info("Health check endpoint called")
    return {"message": "Hello form Real-time Service (FastAPI)"}
