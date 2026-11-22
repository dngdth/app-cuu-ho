# XGBoost/Train_Model_XGBoost.py

import pandas as pd
import numpy as np
import joblib  # Thư viện giúp lưu/đọc model siêu nhanh
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer


# ==============================================================================
# 1. HÀM NỘI BỘ: XỬ LÝ DỮ LIỆU
# ==============================================================================
def _process_features(df):
    """Xử lý dữ liệu thô thành features (Dùng chung cho Train & Predict)"""
    df = df.copy()

    if "label" in df.columns:
        df["label"] = df["label"].astype(str).str.strip().str.upper()
    if "confident" in df.columns:
        df["confident"] = df["confident"].astype(str).str.strip().str.upper()

    cols_1 = ["lương thực & nước uống", "thuốc men & hỗ trợ y tế", "chỗ ở & nơi trú ẩn"]
    cols_2 = [
        "phương tiện & cứu hộ",
        "vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)",
    ]

    for c in cols_1 + cols_2 + ["affected_people"]:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["humanitarian_need_score"] = df[cols_1].sum(axis=1)
    df["rescue_need_score"] = df[cols_2].sum(axis=1)
    df["affected_people_log"] = np.log1p(df["affected_people"])

    return df


# ==============================================================================
# 2. HÀM TRAIN & LƯU MODEL
# ==============================================================================
def train(
    df_input,
    save_path="rescue_model.pkl",
    n_estimators=200,
    learning_rate=0.05,
    max_depth=4,
):
    """
    Huấn luyện và lưu model vào file.
    - save_path: Đường dẫn để lưu file model (VD: 'models/my_ai.pkl')
    """
    print(
        f"🔄 Đang huấn luyện mô hình... (Config: n={n_estimators}, lr={learning_rate})"
    )

    # 1. Xử lý dữ liệu
    df = _process_features(df_input)

    if "label" not in df.columns or "confident" not in df.columns:
        raise ValueError("Dữ liệu train thiếu cột 'label' hoặc 'confident'")

    num_features = [
        "disaster_type",
        "affected_people",
        "deathly",
        "is_isolated",
        "infrastructure_damage",
        "lương thực & nước uống",
        "thuốc men & hỗ trợ y tế",
        "phương tiện & cứu hộ",
        "chỗ ở & nơi trú ẩn",
        "vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)",
        "humanitarian_need_score",
        "rescue_need_score",
        "affected_people_log",
    ]
    cat_features = ["tinh_tp"]

    # 2. Label Encoding
    le_label = LabelEncoder()
    y_label = le_label.fit_transform(df["label"])

    le_conf = LabelEncoder()
    y_conf = le_conf.fit_transform(df["confident"])

    X = df[num_features + cat_features]

    # 3. Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="constant", fill_value=0), num_features),
            (
                "cat",
                Pipeline(
                    steps=[
                        (
                            "imputer",
                            SimpleImputer(strategy="constant", fill_value="Unknown"),
                        ),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                cat_features,
            ),
        ]
    )

    def create_model():
        return Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    GradientBoostingClassifier(
                        n_estimators=n_estimators,
                        learning_rate=learning_rate,
                        max_depth=max_depth,
                        random_state=42,
                    ),
                ),
            ]
        )

    # 4. Train
    model_label = create_model()
    model_label.fit(X, y_label)

    model_conf = create_model()
    model_conf.fit(X, y_conf)

    # 5. Đóng gói và LƯU FILE
    brain = {
        "model_label": model_label,
        "model_conf": model_conf,
        "le_label": le_label,
        "le_conf": le_conf,
    }

    # Lưu xuống ổ cứng
    joblib.dump(brain, save_path)
    print(f"✅ Đã lưu model thành công tại: {save_path}")

    return brain


# ==============================================================================
# 3. HÀM DỰ ĐOÁN (TỰ ĐỘNG LOAD MODEL)
# ==============================================================================


def predict(data_input: pd.DataFrame | dict, model_path: str):
    """
    Dự đoán từ dữ liệu mới.
    - model_input: Có thể là biến 'brain' (dict) HOẶC đường dẫn file (str) (VD: 'rescue_model.pkl')
    - data_input: Dữ liệu cần dự đoán (Dict hoặc DataFrame)
    """

    # A. Xử lý Model đầu vào
    # Khởi tạo model
    brain = joblib.load(model_path)

    # B. Chuẩn bị dữ liệu
    if isinstance(data_input, dict):
        df = pd.DataFrame([data_input])
    else:
        df = data_input.copy()

    df = _process_features(df)

    # C. Dự đoán
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
    if isinstance(data_input, dict):
        return urgency[0], float(urgency_prob[0]), confidence[0], float(confidence_prob[0])
    return urgency, urgency_prob, confidence, confidence_prob
