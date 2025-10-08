from fastapi import FastAPI
import logging

from src.api.health import router as health_router
from src.api.predict import router as predict_router

log = logging.getLogger(__name__)

app = FastAPI(title="ML TI Incident Classifier API", version="0.1.0")

# Mount the API router under /api
app.include_router(health_router)
app.include_router(predict_router)

# # Load model once at startup using path relative to this file (src/)
# MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
# model = None
# try:
#     with MODEL_PATH.open("rb") as f:
#         model = pickle.load(f)
#         log.info("Loaded model from %s", MODEL_PATH)
# except FileNotFoundError:
#     log.error("Model file not found at %s", MODEL_PATH)
# except Exception as e:
#     log.exception("Failed loading model: %s", e)


# @app.post("/predict", tags=["predict"])
# def predict(req: PredictRequest):
#     """Predict endpoint that returns model label or raises 500 if model missing."""

#     if model is None:
#         # Fail fast with a helpful error so tests/clients can see what's wrong
#         raise HTTPException(status_code=500, detail=f"Model not loaded from {MODEL_PATH}")

#     # Create a feature vector using the defined fields in the request
#     features = [
#         req.source,
#         req.environment,
#         req.severity,
#         req.metric_name,
#         req.ci,
#         req.maintenace,
#     ]

#     # Some models expect numeric features; this keeps current behavior but may need adapting.
#     try:
#         prediction = model.predict([features])
#     except Exception as e:
#         log.exception("Model prediction failed: %s", e)
#         raise HTTPException(status_code=500, detail="Model prediction failed")

#     return {"label": prediction[0]}
