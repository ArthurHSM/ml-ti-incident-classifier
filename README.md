# ml-ti-incident-classifier
Repositório destinado ao projeto do Tech Challenge da fase 03 do curso de pós graduação de Machine Learning Engineering da FIAP. O objetivo é criar um algoritmo de machine learning capaz de classificar incidentes em ambientes de TI.

## Sobre a API

### Setup environment

```sh
source ./venv/bin/activate && \
pip install -r requirements.txt
```

### Testar

```sh
pytest
```

### Executar localmente

```sh
uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
```

### Compilar e Executar em ambiente de container

```sh
docker build -t ml-ti-incident-classifier:latest .
docker run --rm -p 8000:8000 ml-ti-incident-classifier:latest
```
