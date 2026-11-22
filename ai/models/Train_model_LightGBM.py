import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from lightgbm import LGBMClassifier, early_stopping, log_evaluation
import lightgbm as lgb

# ==============================================================================
# 1. HÀM NỘI BỘ: XỬ LÝ DỮ LIỆU (PRIVATE – DÙNG CHUNG)
# ==============================================================================
def _process_features(df):
    """
    Hàm nội bộ: xử lý + feature engineering
    Dùng CHUNG cho train & predict
    """
    df = df.copy()

    # --- Chuẩn hóa chuỗi ---
    if 'label' in df.columns:
        df['label'] = df['label'].astype(str).str.strip().str.upper()
    if 'confident' in df.columns:
        df['confident'] = df['confident'].astype(str).str.strip().str.upper()

    # --- Các cột nhu cầu ---
    cols_1 = ['lương thực & nước uống', 'thuốc men & hỗ trợ y tế', 'chỗ ở & nơi trú ẩn']
    cols_2 = ['phương tiện & cứu hộ',
              'vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)']

    for c in cols_1 + cols_2 + ['affected_people']:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # --- Feature engineering ---
    df['humanitarian_need_score'] = df[cols_1].sum(axis=1)
    df['rescue_need_score'] = df[cols_2].sum(axis=1)
    df['affected_people_log'] = np.log1p(df['affected_people'])

    # location -> binary
    if 'location' in df.columns:
        df['location'] = df['location'].notna().astype(int)

    return df


# ==============================================================================
# 2. TRAIN (PUBLIC API) – LIGHTGBM
# ==============================================================================
def train(df_input: pd.DataFrame, save_path="rescue_model_lightGBM.pkl"):
    """
    Train 2 LightGBM models:
    - urgency (3 class)
    - confidence (binary)
    """

    print(">>> Start training LightGBM models...")

    df = _process_features(df_input)

    if 'label' not in df.columns or 'confident' not in df.columns:
        raise ValueError("Train data must contain 'label' and 'confident'")

    # 1. Features
    urgency_features = [
        'affected_people', 'deathly', 'is_isolated',
        'infrastructure_damage',
        'lương thực & nước uống',
        'thuốc men & hỗ trợ y tế',
        'phương tiện & cứu hộ',
        'chỗ ở & nơi trú ẩn',
        'vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)',
        'humanitarian_need_score',
        'rescue_need_score',
        'affected_people_log'
    ]

    confidence_features = [
        'has_emotional_terms',
        'has_emphasis',
        'contact',
        'location'
    ]

    # 2. Label Encoding
    le_u = LabelEncoder()
    y_u = le_u.fit_transform(df['label'])

    le_c = LabelEncoder()
    y_c = le_c.fit_transform(df['confident'])

    # Ensure confidence features are strings before creating X so imputers expecting strings don't receive numeric dtypes
    df[confidence_features] = df[confidence_features].astype("string")

    X = df[urgency_features + confidence_features]

    # 3. Pipeline

    preprocessor = ColumnTransformer(
        transformers=[
            ("urgency", SimpleImputer(strategy="constant", fill_value=0), urgency_features),
            (
                "confidence",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                confidence_features,
            ),
        ]
    )

    def create_model(objective='multiclass', num_class=None):
        """Create a pipeline with LGBMClassifier configured for the desired objective.
        objective: 'multiclass' or 'binary' (or any other lightgbm objective)
        num_class: required when objective is 'multiclass'
        """
        clf_params = dict(
            n_estimators=1000,
            learning_rate=0.05,
            num_leaves=15,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight='balanced',
            random_state=42,
        )

        if objective == 'multiclass':
            clf_params.update({'objective': 'multiclass', 'metric': 'multi_logloss'})
            if num_class is not None:
                clf_params['num_class'] = num_class
        elif objective == 'binary':
            clf_params.update({'objective': 'binary', 'metric': 'binary_logloss'})
        else:
            clf_params.update({'objective': objective})

        return Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", LGBMClassifier(**clf_params)),
            ]
        )
    
    # 4. Diagnostics & Train
    print("Urgency label distribution:", np.unique(y_u, return_counts=True))
    print("Confidence label distribution:", np.unique(y_c, return_counts=True))
    print("Feature summary:\n", X.describe(include='all').T)

    if len(np.unique(y_u)) < 2:
        raise ValueError("Urgency target has less than 2 classes; cannot train multiclass model")
    if len(np.unique(y_c)) < 2:
        raise ValueError("Confidence target has less than 2 classes; cannot train binary model")

    num_classes = len(le_u.classes_)

    model_label = create_model(objective='multiclass', num_class=num_classes)
    model_label.fit(X, y_u)

    model_conf = create_model(objective='binary')
    model_conf.fit(X, y_c)

    print(">>> Training completed")

    brain = {
        "model_label": model_label,
        "model_conf": model_conf,
        "le_label": le_u,
        "le_conf": le_c,
    }

    joblib.dump(brain, save_path)
    print(f"✅ Đã lưu model thành công tại: {save_path}")

    return brain


# ==============================================================================
# 3. PREDICT (PUBLIC API)
# ==============================================================================
def predict(input_data: pd.DataFrame | dict, model_path: str):
    """
    Predict urgency & confidence using trained LightGBM models
    """
    # Check model file existence and basic validity before loading
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if os.path.getsize(model_path) == 0:
        raise EOFError(f"Model file is empty or corrupted: {model_path}")

    try:
        brain = joblib.load(model_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load model from {model_path}: {e}") from e

    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])
    elif isinstance(input_data, str):
        # treat as path to csv file
        if os.path.exists(input_data):
            df = pd.read_csv(input_data)
        else:
            raise ValueError(f"input_data string is not a file path: {input_data}")
    else:
        df = input_data.copy()

    df = _process_features(df)

    # Ensure confidence feature dtypes match training (string) to avoid imputer type errors
    confidence_features = ['has_emotional_terms', 'has_emphasis', 'contact', 'location']
    for c in confidence_features:
        if c in df.columns:
            df[c] = df[c].astype("string")

    lbl_model = brain["model_label"]
    conf_model = brain["model_conf"]
    lbl_enc = brain["le_label"]
    conf_enc = brain["le_conf"]

    p_lbl_idx = lbl_model.predict(df)
    prob_lbl = np.max(lbl_model.predict_proba(df), axis=1)

    p_conf_idx = conf_model.predict(df)
    prob_conf = np.max(conf_model.predict_proba(df), axis=1)

    urgency = lbl_enc.inverse_transform(p_lbl_idx)
    urgency_prob = np.round(prob_lbl, 4)
    confidence = conf_enc.inverse_transform(p_conf_idx)
    confidence_prob = np.round(prob_conf, 4)
    if isinstance(input_data, dict):
        return urgency[0], float(urgency_prob[0]), confidence[0], float(confidence_prob[0])
    
    return urgency, urgency_prob, confidence, confidence_prob

if __name__ == "__main__":
    df = pd.read_csv("data/dataset/data_cleaned.csv")
    model_path = "ai/rescue_model_lightGBM.pkl"

    # Run a sample prediction using the first row
    sample = df.iloc[0].to_dict()
    urgency, urgency_prob, confidence, confidence_prob = predict(sample, model_path)
    print("Sample Prediction:", urgency, urgency_prob, confidence, confidence_prob)
