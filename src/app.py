from fastapi import FastAPI
import logging

from src.api.health import router as health_router
from src.api.predict import router as predict_router

log = logging.getLogger(__name__)

app = FastAPI(title="ML TI Incident Classifier API", version="0.1.0")

# Mount the API router under /api
app.include_router(health_router)
app.include_router(predict_router)

log.info("API routers mounted.")
