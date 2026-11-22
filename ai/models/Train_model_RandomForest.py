import pandas as pd
import numpy as np
import joblib

from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer


# ==============================================================================
# 1. XỬ LÝ DỮ LIỆU (DÙNG CHUNG CHO TRAIN & PREDICT)
# ==============================================================================
def _process_features(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa & feature engineering"""

    df = df.copy()

    # Chuẩn hóa label
    if "label" in df.columns:
        df["label"] = df["label"].astype(str).str.strip().str.upper()
    if "confident" in df.columns:
        df["confident"] = df["confident"].astype(str).str.strip().str.upper()

    if "disaster_type" not in df.columns:
        df["disaster_type"] = -1
    else:
        # Chuyển sang số, nếu lỗi (vd: chuỗi rỗng) -> NaN -> sau đó điền -1
        df["disaster_type"] = pd.to_numeric(df["disaster_type"], errors='coerce').fillna(-1)

    cols_1 = ["lương thực & nước uống", "thuốc men & hỗ trợ y tế", "chỗ ở & nơi trú ẩn"]
    cols_2 = [
        "phương tiện & cứu hộ",
        "vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)",
    ]

    important_cols = ["affected_people", "deathly", "is_isolated", "infrastructure_damage"]
    for c in cols_1 + cols_2 + important_cols:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Feature engineering
    df["humanitarian_need_score"] = df[cols_1].sum(axis=1)
    df["rescue_need_score"] = df[cols_2].sum(axis=1)
    df["affected_people_log"] = np.log1p(df["affected_people"])

    return df


# ==============================================================================
# 2. TRAIN & SAVE MODEL
# ==============================================================================
def train(
    df_input: pd.DataFrame,
    save_path="/home/nguyenhuynh/Documents/appcuuho/be/ai/models/rescue_model_rf.pkl",
    n_estimators=300,
    max_depth=15,
    min_samples_split=5,
):
    """
    Huấn luyện Random Forest & lưu model (1 file duy nhất)
    """

    print(
        f"🌲 Training RandomForest (n={n_estimators}, depth={max_depth})..."
    )

    df = _process_features(df_input)

    if "label" not in df.columns or "confident" not in df.columns:
        raise ValueError("Dữ liệu train thiếu cột 'label' hoặc 'confident'")

    # ---------------- FEATURES ----------------
    num_features = [
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

    cat_features = ["tinh_tp", "disaster_type"]

    X = df[num_features + cat_features]

    # ---------------- TARGET ----------------
    le_label = LabelEncoder()
    le_conf = LabelEncoder()

    y_label = le_label.fit_transform(df["label"])
    y_conf = le_conf.fit_transform(df["confident"])

    # ---------------- PREPROCESS ----------------
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="constant", fill_value=0), num_features),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                cat_features,
            ),
        ]
    )

    def build_model():
        return Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        min_samples_split=min_samples_split,
                        random_state=42,
                        n_jobs=-1,
                        class_weight="balanced",
                    ),
                ),
            ]
        )

    # ---------------- TRAIN 2 MODELS ----------------
    model_label = build_model()
    model_label.fit(X, y_label)

    model_conf = build_model()
    model_conf.fit(X, y_conf)

    brain = {
        "model_label": model_label,
        "model_conf": model_conf,
        "le_label": le_label,
        "le_conf": le_conf,
    }

    joblib.dump(brain, save_path)
    print(f"✅ RandomForest model saved at: {save_path}")

    return brain


# ==============================================================================
# 3. PREDICT (TỰ LOAD MODEL)
# ==============================================================================
def predict(data_input: dict | pd.DataFrame, model_path: str):
    """
    Dự đoán từ dữ liệu mới (Dict hoặc DataFrame)
    """

    brain = joblib.load(model_path)

    if isinstance(data_input, dict):
        df = pd.DataFrame([data_input])
    else:
        df = data_input.copy()

    df = _process_features(df)

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


# import os

# # ==============================================================================
# # 4. HÀM MAIN (CHẠY CHƯƠNG TRÌNH)
# # ==============================================================================
# def main():
#     # --- CẤU HÌNH ĐƯỜNG DẪN ---
#     # Thay đổi đường dẫn file dữ liệu thật của bạn ở đây (nếu có)
#     DATA_PATH = "/home/nguyenhuynh/Documents/appcuuho/be/data/dataset/data_v5.csv" 
    
#     # Đường dẫn lưu model (dùng đường dẫn tương đối để tránh lỗi trên máy khác)
#     MODEL_DIR = "models"
#     MODEL_PATH = os.path.join(MODEL_DIR, "rescue_model_rf.pkl")

#     # Tạo thư mục chứa model nếu chưa có
#     if not os.path.exists(MODEL_DIR):
#         os.makedirs(MODEL_DIR)
#         print(f"📁 Đã tạo thư mục: {MODEL_DIR}")

#     # --- BƯỚC 1: CHUẨN BỊ DỮ LIỆU ---
#     df_train = None

#     if os.path.exists(DATA_PATH):
#         print(f"📖 Đang đọc dữ liệu từ: {DATA_PATH}")
#         # Hỗ trợ cả csv và excel
#         if DATA_PATH.endswith(".csv"):
#             df_train = pd.read_csv(DATA_PATH)
#         else:
#             df_train = pd.read_excel(DATA_PATH)
#     else:
#         print(f"⚠️ Không tìm thấy file '{DATA_PATH}'. Đang tạo dữ liệu giả lập để test...")
#         # Tạo dữ liệu giả lập (Dummy Data)
#         df_train = pd.DataFrame({
#             "affected_people": [10, 5000, 150, 20, 10000, 5],
#             "deathly": [0, 50, 2, 0, 100, 0],
#             "is_isolated": [0, 1, 1, 0, 1, 0],
#             "infrastructure_damage": [10, 95, 50, 5, 90, 2],
#             "tinh_tp": ["Hà Nội", "Lào Cai", "Yên Bái", "Đà Nẵng", "Cao Bằng", "HCM"],
#             "disaster_type": [1, 2, 2, 1, 2, 0], 
#             "lương thực & nước uống": [1, 1, 1, 0, 1, 0],
#             "thuốc men & hỗ trợ y tế": [0, 1, 0, 0, 1, 0],
#             "chỗ ở & nơi trú ẩn": [0, 1, 1, 0, 1, 0],
#             "phương tiện & cứu hộ": [0, 1, 1, 0, 1, 0],
#             "vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)": [1, 1, 0, 0, 1, 0],
#             # Label
#             "label": ["Low", "Critical", "High", "Low", "Critical", "Low"], 
#             "confident": ["High", "High", "Medium", "Low", "High", "Low"]
#         })

#     print(f"📊 Kích thước dữ liệu train: {df_train.shape}")

#     # --- BƯỚC 2: HUẤN LUYỆN MODEL ---
#     try:
#         train(
#             df_input=df_train,
#             save_path=MODEL_PATH,
#             n_estimators=100, # Giảm xuống 100 để test cho nhanh
#             max_depth=10
#         )
#     except Exception as e:
#         print(f"❌ Lỗi khi train: {e}")
#         return

#     # --- BƯỚC 3: TEST DỰ ĐOÁN (PREDICT) ---
#     print("\n🔍 --- CHẠY THỬ PREDICT VỚI DỮ LIỆU MỚI ---")
    
#     # Dữ liệu test: Một trường hợp rất khẩn cấp
#     sample_input = {
#         "affected_people": 2000,
#         "deathly": 10,
#         "is_isolated": 1,          # Bị cô lập
#         "infrastructure_damage": 80,
#         "tinh_tp": "Lào Cai",
#         "disaster_type": 2,        # Sạt lở
#         "lương thực & nước uống": 1,
#         "thuốc men & hỗ trợ y tế": 1
#     }

#     try:
#         urgency, urgency_prob, conf, conf_prob = predict(sample_input, MODEL_PATH)
        
#         print(f"Input: {sample_input}")
#         print("-" * 30)
#         print(f"📢 Mức độ khẩn cấp : {urgency} (Độ tin cậy model: {urgency_prob*100:.2f}%)")
#         print(f"✅ Độ xác thực tin : {conf} (Độ tin cậy model: {conf_prob*100:.2f}%)")
#         print("-" * 30)
        
#     except Exception as e:
#         print(f"❌ Lỗi khi predict: {e}")

# # ==============================================================================
# # ENTRY POINT
# # ==============================================================================
# if __name__ == "__main__":
#     main()
