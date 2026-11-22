import sys

sys.path.append("/home/nguyenhuynh/Documents/appcuuho/be")

from ai.models.Train_model_LightGBM import predict as predict_lightGBM

test_data = [
    # CASE 1: Mức độ CAO (Lũ lụt, nhiều người bị kẹt, có người già/trẻ em, thiếu lương thực)
    {
        "content": "Cứu gấp, ngõ 770 Dương Tự Minh, 35 người kẹt, có trẻ 6 tháng, nước ngập tầng 2, không thức ăn",
        "disaster_type": 2,  # Lũ lụt
        "affected_people": 35,  # Rất đông người
        "deathly": 0,  # Chưa có người chết (nhưng nguy hiểm)
        "is_isolated": 1,  # Bị cô lập
        "infrastructure_damage": 1,  # Nhà cửa hư hại
        "lương thực & nước uống": 1,  # Cần gấp
        "phương tiện & cứu hộ": 1,  # Cần xuồng
        "tinh_tp": "Thái Nguyên",  # Địa điểm
        # Confidence features (used by the confidence model)
        "has_emotional_terms": 1,
        "has_emphasis": 1,
        "contact": "+84123456789",
        "location": "Ngõ 770 Dương Tự Minh, Thái Nguyên",
    },
    # CASE 2: Mức độ TRUNG BÌNH (Ít người, chưa nguy hiểm tính mạng ngay lập tức)
    {
        "content": "Khu vực Đồng Hỷ, nhà mình 3 người lớn bị kẹt, hiện tại vẫn ổn nhưng hết đồ ăn từ hôm qua",
        "disaster_type": 2,
        "affected_people": 3,
        "deathly": 0,
        "is_isolated": 1,
        "infrastructure_damage": 0,
        "lương thực & nước uống": 1,  # Chỉ cần lương thực
        "phương tiện & cứu hộ": 0,  # Chưa cần cứu hộ gấp
        "tinh_tp": "Thái Nguyên",
        "has_emotional_terms": 0,
        "has_emphasis": 0,
        "contact": "",
        "location": "Khu Đồng Hỷ, Thái Nguyên",
    },
    # CASE 3: Mức độ THẤP (Thông báo tin tức hoặc xin hỗ trợ vật dụng sau bão)
    {
        "content": "Cần xin ít quần áo cũ và chăn màn cho bà con vùng lũ đã rút nước",
        "disaster_type": 0,
        "affected_people": 0,
        "deathly": 0,
        "is_isolated": 0,  # Không bị cô lập
        "infrastructure_damage": 0,
        "lương thực & nước uống": 0,
        "vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)": 1,  # Cần vật dụng
        "tinh_tp": "Hà Nội",
        "has_emotional_terms": 0,
        "has_emphasis": 0,
        "contact": "",
        "location": "Hà Nội",
    },
]
for item in test_data:
    (
        urgency_score_lightGBM,
        urgency_prob_lightGBM,
        reliability_score_lightGBM,
        reliability_prob_lightGBM,
    ) = predict_lightGBM(
        item, "/home/nguyenhuynh/Documents/appcuuho/be/ai/rescue_model_lightGBM.pkl"
    )
    print(f"Urgency label: {urgency_score_lightGBM}")
    print(f"Urgency probability: {urgency_prob_lightGBM}")
    print(f"Reliability label: {reliability_score_lightGBM}")
    print(f"Reliability probability: {reliability_prob_lightGBM}\n")
