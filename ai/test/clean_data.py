import pandas as pd
import re
from pydantic import BaseModel
from module.agent import Agent

# Khởi tạo agent
agent = Agent()

# Prompt bóc tách địa chỉ
prompt_template = """
Bạn là một trợ lý phân tích dữ liệu cứu hộ. Hãy bóc tách địa chỉ sau thành định dạng JSON.
Địa chỉ: {location}

Yêu cầu trả về JSON với các trường:
- "tinh_tp": Tỉnh hoặc Thành phố trực thuộc trung ương.
- "quan_huyen": Quận, Huyện hoặc Thị xã.
- "phuong_xa": Phường, Xã hoặc Thị trấn.
- "nha": Số nhà, ngõ, tên đường hoặc các mô tả chi tiết vị trí nhỏ hơn xã.

Chỉ trả về duy nhất khối JSON, không giải thích gì thêm.
Kết quả JSON:
"""

class Response(BaseModel):
    tinh_tp: str
    quan_huyen: str
    phuong_xa: str
    nha: str


def data_clean(df: pd.DataFrame) -> pd.DataFrame:
    # =======================
    # 1. THỐNG KÊ BAN ĐẦU
    # =======================
    count_before = len(df)

    # =======================
    # 2. LỌC TRÙNG CONTENT
    # =======================
    df = df.drop_duplicates(subset=['content'], keep='first').copy()
    count_after = len(df)

    # =======================
    # 3. MÃ HÓA CONTACT
    # =======================
    def contact_has_phone(val):
        if pd.isna(val) or val == '[]':
            return 0
        digits = re.sub(r'[^0-9]', '', str(val))
        return 1 if len(digits) >= 7 else 0

    if 'contact' in df.columns:
        df['contact'] = df['contact'].apply(contact_has_phone)
    else:
        df['contact'] = 0

    # =======================
    # 4. BÓC TÁCH ĐỊA CHỈ
    # =======================
    def parse_address_local(location: str) -> dict:
        if pd.isna(location) or str(location).strip() == "":
            return {
                "tinh_tp": None,
                "quan_huyen": None,
                "phuong_xa": None,
                "nha": None
            }
        try:
            user_prompt = prompt_template.format(location=location)
            message = agent.generate_sync(
                user_prompt=user_prompt,
                response_schema=Response
            )
            return message.dict() if hasattr(message, "dict") else dict(message)
        except Exception as e:
            print(f"Lỗi dòng: {location} -> {e}")
            return {
                "tinh_tp": None,
                "quan_huyen": None,
                "phuong_xa": None,
                "nha": None
            }

    print(f"Bắt đầu bóc tách {len(df)} địa chỉ...")

    results = [parse_address_local(loc) for loc in df['location'].tolist()]
    df_address = pd.json_normalize(results)

    # =======================
    # 5. GỘP DATAFRAME
    # =======================
    df_final = pd.concat(
        [df.reset_index(drop=True), df_address],
        axis=1
    )

    # =======================
    # 6. LOG
    # =======================
    print(f"Số dòng ban đầu: {count_before}")
    print(f"Số dòng sau khi lọc trùng: {count_after}")
    print(f"Đã xóa: {count_before - count_after} dòng trùng")

    return df_final
