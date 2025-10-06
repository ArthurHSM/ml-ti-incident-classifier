# ML TI Incident Classifier - API

This folder contains a minimal FastAPI application used as an example.

Run locally (from project root):

```bash
python -m pip install -r src/requirements.txt
uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
```

Endpoints:
- GET / -> health check
- POST /predict -> example predict endpoint (JSON body: {"text": "..."})
- GET /api/example -> example router endpoint
