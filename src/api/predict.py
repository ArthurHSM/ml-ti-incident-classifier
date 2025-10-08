import joblib
import pandas as pd
import re
import xgboost as xgb

from pathlib import Path

from fastapi import APIRouter

from scipy.sparse import csr_matrix, hstack

from sklearn.preprocessing import OneHotEncoder

from src.model.predict_request import PredictRequest

router = APIRouter(prefix="/predict", tags=["predict"])

# compute package-relative paths (src/)
BASE_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = BASE_DIR / "bin"
OHE_PATH = BIN_DIR / "ohe_category_map.pkl"
MODEL_PATH = BIN_DIR / "xgb_champion_final.pkl"

INPUT_COLS_API = ['source', 'environment', 'severity', 'metric_name', 'ci', 'maintenance']
CATEGORICAL_COLS = ['source', 'environment', 'severity', 'metric_name', 'ci_tratado']
THRESHOLD_BUSINESS = 0.75

# Lazy-load OHE map/transformer so import-time missing files don't crash the app
_OHE_CATEGORY_MAP = None
_ohe_transformer = None

def _ensure_ohe():
    global _OHE_CATEGORY_MAP, _ohe_transformer
    if _ohe_transformer is not None and _OHE_CATEGORY_MAP is not None:
        return
    if not OHE_PATH.exists():
        raise FileNotFoundError(f"OHE category map not found at {OHE_PATH}")
    _OHE_CATEGORY_MAP = joblib.load(OHE_PATH)
    _ohe_transformer = OneHotEncoder(
        categories=[_OHE_CATEGORY_MAP[col] for col in CATEGORICAL_COLS],
        handle_unknown='ignore',
        sparse_output=False
    )
    dummy_data_for_fit = pd.DataFrame([
        [_OHE_CATEGORY_MAP[col][0] for col in CATEGORICAL_COLS]
    ], columns=CATEGORICAL_COLS)
    _ohe_transformer.fit(dummy_data_for_fit.values)

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

def prepare_alert_for_model(alert_data_dict: PredictRequest) -> csr_matrix:
    """
    Função principal que replica Feature Engineering para um único alerta.
    Retorna uma matriz esparsa (CSR).
    """

    # 1. Inicialização do DataFrame a partir do JSON (usa as colunas de entrada da API)
    df_alert = pd.DataFrame([alert_data_dict], columns=INPUT_COLS_API)

    # 2. ETAPA DE PRÉ-PROCESSAMENTO/TRANSFORMAÇÃO (Regras de Limpeza)

    # a. Criação da feature 'ci_tratado' (inclui imputação e limpeza)
    df_alert['ci_tratado'] = df_alert['ci'].apply(_process_ci_column)

    # b. Replicar a feature 'maintenance_int' (Binária)
    df_alert['maintenance_int'] = df_alert['maintenance'].apply(
        lambda x: 1 if str(x).lower() == 'true' else 0
    )

    # 3. ETAPA DE VETORIZAÇÃO (One-Hot Encoding e Concatenação)

    categorical_data = df_alert[CATEGORICAL_COLS]

    # Ensure OHE transformer is ready
    try:
        _ensure_ohe()
    except FileNotFoundError as e:
        raise

    # Aplica o OHE (Transforma em matriz esparsa, usando .values)
    ohe_features = _ohe_transformer.transform(categorical_data.values)

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

    return final_vector

def get_model_decision(alert_data_dict: PredictRequest) -> dict:
    """
    Integra o pré-processamento com a previsão e a regra de negócio.
    Esta função simula o endpoint final da API.
    """
    # --- 1. Carregar o modelo ---
    # A API idealmente faria isso APENAS uma vez na inicialização,
    # mas fazemos aqui para o teste:
    try:
        if not MODEL_PATH.exists():
            return {"error": f"Model file not found at {MODEL_PATH}"}, 500
        loaded_model = joblib.load(MODEL_PATH)
    except Exception as e:
        return {"error": f"Failed loading model: {e}"}, 500

    # 2. Pré-processar o alerta para obter o vetor de features
    model_input_vector = prepare_alert_for_model(alert_data_dict)

    # 3. Prever a probabilidade usando o modelo carregado
    # O .predict_proba retorna a probabilidade da classe 0 e 1; pegamos apenas a classe 1 [:, 1]
    probability = loaded_model.predict_proba(model_input_vector)[:, 1][0]

    # 4. Aplicar a Regra de Negócio (Threshold)
    is_incident = probability >= THRESHOLD_BUSINESS

    # 5. Retorno formatado para a API
    return {
        "is_incident": bool(is_incident),
        "probability": float(probability),
        "decision_threshold": THRESHOLD_BUSINESS
    }

@router.post("/", tags=["predict"])
def predict(req: PredictRequest):
    return get_model_decision(req)