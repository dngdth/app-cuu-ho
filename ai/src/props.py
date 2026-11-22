REQUIRED_KEYS = [
    "location",
    "contact",
    "disaster_type",
    "affected_people",
    "infrastructure_damage",
    "needs",
    "is_isolated",
    "deathly",
    "map_link",
]

# Giá trị hợp lệ cho needs
ALLOWED_NEEDS = [
    "lương thực & nước uống",
    "thuốc men & hỗ trợ y tế",
    "chỗ ở & nơi trú ẩn",
    "phương tiện & cứu hộ",
    "liên lạc & thông tin",
    "vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)",
]

# Giá trị hợp lệ cho disaster_type
ALLOWED_DISASTER_TYPES = [
    "lũ lụt",
    "sạt lở",
    "ngập nước",
    "bão",
    "lốc xoáy",
    "động đất",
    "cháy",
    "cháy rừng",
    "hạn hán",
    "sóng thần",
    "không xác định",
]

# Kiểu dữ liệu mong muốn
EXPECTED_TYPES = {
    "location": (str, type(None)),
    "contact": list,
    "disaster_type": list,  # Đổi từ (str, type(None)) thành list
    "affected_people": (int, type(None)),
    "infrastructure_damage": bool,
    "needs": list,
    "is_isolated": bool,
    "deathly": bool,
    "map_link": (str, type(None)),
}


STRING_EXTRACT_FEATURE = ["has_emergency_terms", "has_emotional_terms", "has_emphasis"]
