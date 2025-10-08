FROM python:3.11-slim

# Update OS packages and install build deps
RUN apt-get update && apt-get upgrade -y && \
    apt-get install --no-install-recommends -y gcc libffi-dev build-essential libssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt /app/requirements.txt

# Install runtime deps
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt 

# Copy application code
COPY src /app/src

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
