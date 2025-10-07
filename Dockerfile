FROM python:3.13-alpine

# Update OS packages and install build deps
RUN apk update && apk upgrade --available && \
    apk add --no-cache --virtual .build-deps gcc libffi-dev musl-dev openssl-dev

WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt /app/requirements.txt

# Install runtime deps
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apk del .build-deps

# Copy application code
COPY src /app/src

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
