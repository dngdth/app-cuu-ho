"""
Hàm trích xuất thông tin từ comment để phân tích cứu hộ
"""

import asyncio
import os
import sys
from typing import Dict


from .LangchainClient import get_client
from .props import (
    REQUIRED_KEYS,
    EXPECTED_TYPES,
    ALLOWED_NEEDS,
    ALLOWED_DISASTER_TYPES,
)
from .prompts_utils import (
    get_extract_system_prompt,
    get_extract_prompt,
    validate_json_output,
    extract_string_features,
)
from .validate import (
    validate_keys,
    validate_needs,
    validate_types,
    clean_data,
    validate_disaster_type,
)


async def extract_emergency_info(text: str, max_retries: int = 3) -> Dict:
    """
    Trích xuất thông tin khẩn cấp từ comment/text

    Args:
        text: Nội dung comment cần phân tích
        max_retries: Số lần thử lại nếu JSON không hợp lệ

    Returns:
        Dict chứa các trường:
        - location: Địa điểm (str hoặc None)
        - contact: Danh sách số điện thoại/link liên hệ (list)
        - disaster_type: Loại thiên tai (str)
        - affected_people: Số người bị ảnh hưởng (int hoặc None)
        - infrastructure_damage: Cơ sở hạ tầng bị hư hại (bool)
        - needs: Danh sách nhu cầu cứu trợ (list)
        - is_isolated: Có bị cô lập không (bool)
        - deathly: Có nguy hiểm đến tính mạng không (bool)
        - has_emergency_terms: Có từ khẩn cấp không (bool)
        - has_emotional_terms: Có từ cảm xúc không (bool)
        - has_emphasis: Có nhấn mạnh không (bool)
    """

    client = get_client()
    # Retry loop để tăng độ chính xác
    for attempt in range(1, max_retries + 1):
        try:
            # Gọi LLM để trích xuất thông tin
            res = await client.generate(
                system_prompt=get_extract_system_prompt(),
                user_prompt=get_extract_prompt(text),
            )

            # Validate JSON
            data = validate_json_output(res)
            if not data:
                print(f"[WARN] Attempt {attempt}: JSON rỗng")
                continue

            # Chuẩn hóa dữ liệu
            data = clean_data(data)

            # Validate các trường
            if (
                validate_keys(data, REQUIRED_KEYS)
                and validate_types(data, EXPECTED_TYPES)
                and validate_needs(data, ALLOWED_NEEDS)
                and validate_disaster_type(data, ALLOWED_DISASTER_TYPES)
            ):
                # Trích xuất thêm các đặc trưng từ string
                features = extract_string_features(text)
                data.update(features)

                return data

            print(f"[WARN] Attempt {attempt}: JSON không hợp lệ, retry...")

        except Exception as e:
            print(f"[LỖI] Attempt {attempt}: {e}")

    raise ValueError("Không trích xuất được JSON hợp lệ sau các lần thử")
