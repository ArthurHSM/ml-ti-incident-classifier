from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
from pathlib import Path
import logging

log = logging.getLogger(__name__)

app = FastAPI(title="ML TI Incident Classifier API", version="0.1.0")


@app.get("/", tags=["health"])
def read_root():
    """Health-check / root endpoint"""
    return {"status": "ok", "service": "ml-ti-incident-classifier"}


class PredictRequest(BaseModel):
    source: str | None = None
    environment: str | None = None
    severity: str | None = None
    metric_name: str | None = None
    ci: str | None = None
    maintenace: bool | None = None


# Load model once at startup using path relative to this file (src/)
MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
model = None
try:
    with MODEL_PATH.open("rb") as f:
        model = pickle.load(f)
        log.info("Loaded model from %s", MODEL_PATH)
except FileNotFoundError:
    log.error("Model file not found at %s", MODEL_PATH)
except Exception as e:
    log.exception("Failed loading model: %s", e)


@app.post("/predict", tags=["predict"])
def predict(req: PredictRequest):
    """Predict endpoint that returns model label or raises 500 if model missing."""

    if model is None:
        # Fail fast with a helpful error so tests/clients can see what's wrong
        raise HTTPException(status_code=500, detail=f"Model not loaded from {MODEL_PATH}")

    # Create a feature vector using the defined fields in the request
    features = [
        req.source,
        req.environment,
        req.severity,
        req.metric_name,
        req.ci,
        req.maintenace,
    ]

    # Some models expect numeric features; this keeps current behavior but may need adapting.
    try:
        prediction = model.predict([features])
    except Exception as e:
        log.exception("Model prediction failed: %s", e)
        raise HTTPException(status_code=500, detail="Model prediction failed")

    return {"label": prediction[0]}
