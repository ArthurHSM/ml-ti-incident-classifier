from pydantic import BaseModel

class PredictRequest(BaseModel):
    source: str | None = None
    environment: str | None = None
    severity: str | None = None
    metric_name: str | None = None
    ci: str | None = None
    maintenace: bool | None = None