import joblib
import logging
import pandas as pd
import re
import xgboost as xgb

from pathlib import Path

from fastapi import APIRouter

from scipy.sparse import csr_matrix, hstack

from sklearn.preprocessing import OneHotEncoder

from src.model.predict_request import PredictRequest

router = APIRouter(prefix="/predict", tags=["predict"])

logger = logging.getLogger(__name__)

# compute package-relative paths (src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# mapa de categorias salvo
try:
    OHE_CATEGORY_MAP = joblib.load(f"{BASE_DIR}/bin/ohe_category_map.pkl")
except FileNotFoundError:
    raise RuntimeError("Erro ao carregar artefatos. Verifique a pasta 'model_artifacts_deploy'.")

# Definições de Colunas
CATEGORICAL_COLS = ['source', 'environment', 'severity', 'metric_name', 'ci_tratado']
# O input da API ainda terá a coluna 'ci' original, mas a saída precisa de 'ci_tratado'
INPUT_COLS_API = ['source', 'environment', 'severity', 'metric_name', 'ci', 'maintenance']
THRESHOLD_NEGOCIO = 0.75

# Instanciação do OHE (Repetido aqui para clareza da função final)
ohe_transformer = OneHotEncoder(
    categories=[OHE_CATEGORY_MAP[col] for col in CATEGORICAL_COLS],
    handle_unknown='ignore',
    sparse_output=False
)

dummy_data_for_fit = pd.DataFrame([
    [OHE_CATEGORY_MAP[col][0] for col in CATEGORICAL_COLS]
], columns=CATEGORICAL_COLS)
ohe_transformer.fit(dummy_data_for_fit.values)

def _process_ci_column(ci_value):
    """
    Função auxiliar para aplicar o tratamento do CI.
    1. Trata nulos/vazios.
    2. Extrai apenas as letras (ex: 'app-7' -> 'app').
    """
    # 1. Imputação de Nulos/Vazios
    if pd.isna(ci_value) or str(ci_value).strip() == '':
        return "unknown_ci"

    # 2. Extração de Apenas Letras (Ex: 'db-42' -> 'db')
    # O regex [a-zA-Z]+ encontra uma ou mais letras no início da string
    match = re.search(r'^[a-zA-Z]+', str(ci_value).lower())

    if match:
        return match.group(0) # Retorna a string de letras (ex: 'app')
    else:
        # Se não encontrar letras (ex: '404-error'), trata como desconhecido
        return "unknown_ci"

def prepare_alert_for_model(alert_data_dict: dict) -> csr_matrix:
    """
    Função principal que replica Feature Engineering para um único alerta.
    Retorna uma matriz esparsa (CSR).
    """

    # 1. Inicialização do DataFrame a partir do JSON (usa as colunas de entrada da API)
    df_alert = pd.DataFrame([alert_data_dict], columns=INPUT_COLS_API)

    logger.info(f"Received alert data: {df_alert.to_dict(orient='records')}")

    # 2. ETAPA DE PRÉ-PROCESSAMENTO/TRANSFORMAÇÃO (Regras de Limpeza)

    # a. Criação da feature 'ci_tratado' (inclui imputação e limpeza)
    df_alert['ci_tratado'] = df_alert['ci'].apply(_process_ci_column)

    # b. Replicar a feature 'maintenance_int' (Binária)
    df_alert['maintenance_int'] = df_alert['maintenance'].apply(
        lambda x: 1 if str(x).lower() == 'true' else 0
    )

    # 3. ETAPA DE VETORIZAÇÃO (One-Hot Encoding e Concatenação)

    categorical_data = df_alert[CATEGORICAL_COLS]


    # Aplica o OHE (Transforma em matriz esparsa, usando .values)
    # Assumimos que ohe_transformer foi inicializado com sparse_output=True
    ohe_features = ohe_transformer.transform(categorical_data.values)

    logger.info(f"OHE transformed features shape: {ohe_features.tolist()}")

    # Converte a feature 'maintenance_int' (Densa) em uma matriz esparsa (CSR)
    maintenance_sparse = csr_matrix(df_alert[['maintenance_int']].values)

    # Concatena (Replica o VectorAssembler) usando hstack (Sparse Horizontal Stack)
    final_vector = hstack([
        ohe_features,
        maintenance_sparse
    ], format='csr')

    # 4. Validação
    if final_vector.shape[1] != 37:
        raise ValueError(f"Dimensão do vetor inválida: {final_vector.shape[1]}. Esperado: 37 features.")

    logger.info(f"Prepared feature vector with shape: {final_vector.toarray()}")

    return final_vector

def get_model_decision(alert_data_dict: dict) -> dict:
    """
    Integra o pré-processamento com a previsão e a regra de negócio.
    Esta função simula o endpoint final da API.
    """
    # --- 1. Carregar o modelo ---
    # A API idealmente faria isso APENAS uma vez na inicialização,
    # mas fazemos aqui para o teste:
    try:
        loaded_model = joblib.load(f"{BASE_DIR}/bin/xgb_champion_final.pkl")
    except FileNotFoundError:
        return {"error": "Arquivo do modelo não encontrado. Verifique o caminho."}, 500

    # 2. Pré-processar o alerta para obter o vetor de features
    model_input_vector = prepare_alert_for_model(alert_data_dict)

    # 3. Prever a probabilidade usando o modelo carregado
    # O .predict_proba retorna a probabilidade da classe 0 e 1; pegamos apenas a classe 1 [:, 1]
    probability = loaded_model.predict_proba(model_input_vector)[:, 1][0]

    # 4. Aplicar a Regra de Negócio (Threshold)
    is_incident = probability >= THRESHOLD_NEGOCIO

    # 5. Retorno formatado para a API
    return {
        "is_incident": bool(is_incident),
        "probability": float(probability),
        "decision_threshold": THRESHOLD_NEGOCIO
    }

@router.post("/", tags=["predict"])
def predict(req: PredictRequest):
    # convert to dict (Pydantic v1)
    req_dict = req.dict(exclude_none=True)

    # now access values safely with .get()
    features = [
        req_dict.get("source"),
        req_dict.get("environment"),
        req_dict.get("severity"),
        req_dict.get("metric_name"),
        req_dict.get("ci"),
        # convert boolean to int if model expects numeric
        int(req_dict.get("maintenace", False)) if req_dict.get("maintenace") is not None else None,
    ]

    return get_model_decision(features)