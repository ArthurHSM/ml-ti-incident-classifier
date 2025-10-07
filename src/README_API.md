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

Docker
------

Build the image (from project root):

```bash
docker build -t ml-ti-incident-classifier:latest .
```

Run with docker:

```bash
docker run --rm -p 8000:8000 ml-ti-incident-classifier:latest
```

Or use docker-compose for a convenient mapping of the local `src/` code into the container (useful for development):

```bash
docker-compose up --build
```

The API will be available at http://127.0.0.1:8000
