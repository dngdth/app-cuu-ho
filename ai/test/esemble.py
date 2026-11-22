import pandas as pd
import numpy as np

def ensemble_predictions(df_results):
    """
    So sánh kết quả từ XGBoost, Random Forest và LightGBM.
    Chọn nhãn từ model có xác suất (probability) cao nhất.
    """

    urgency_probs = ['urgency_prob_xgboost', 'urgency_prob_rf', 'urgency_prob_lgbm']
    urgency_scores = ['urgency_score_xgboost', 'urgency_score_rf', 'urgency_score_lgbm']
    
    # Tìm index của model có xác suất cao nhất cho mỗi dòng
    best_urgency_idx = df_results[urgency_probs].idxmax(axis=1)
    
    # Map index đó sang cột score tương ứng
    df_results['final_urgency_score'] = df_results.apply(
        lambda x: x[best_urgency_idx[x.name].replace('prob', 'score')], axis=1
    )
    df_results['max_urgency_prob'] = df_results[urgency_probs].max(axis=1)

    # 2. Xử lý cho Reliability Score (tương tự)
    reliability_probs = ['reliability_prob_xgboost', 'reliability_prob_rf', 'reliability_prob_lgbm']
    
    best_reliability_idx = df_results[reliability_probs].idxmax(axis=1)
    
    df_results['final_reliability_score'] = df_results.apply(
        lambda x: x[best_reliability_idx[x.name].replace('prob', 'score')], axis=1
    )
    df_results['max_reliability_prob'] = df_results[reliability_probs].max(axis=1)

    return df_results[['final_urgency_score', 'final_reliability_score']]