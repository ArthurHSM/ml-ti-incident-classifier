from fastapi import FastAPI
from pydantic import BaseModel

from .api import example

app = FastAPI(title="ML TI Incident Classifier API", version="0.1.0")

app.include_router(example.router, prefix="/api")


@app.get("/", tags=["health"])
def read_root():
    """Health-check / root endpoint"""
    return {"status": "ok", "service": "ml-ti-incident-classifier"}


class PredictRequest(BaseModel):
    text: str


@app.post("/predict", tags=["predict"])
def predict(req: PredictRequest):
    """Example predict endpoint that returns a dummy label and score.

    This is a placeholder for wiring a real model.
    """
    text = req.text
    # Very naive rule-based placeholder
    label = "incident" if "error" in text.lower() or "fail" in text.lower() else "non-incident"
    score = 0.9 if label == "incident" else 0.1
    return {"label": label, "score": score, "input_length": len(text)}
