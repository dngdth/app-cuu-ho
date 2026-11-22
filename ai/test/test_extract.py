"""
Hàm trích xuất thông tin từ comment để phân tích cứu hộ
"""

import asyncio
import os
import sys
from typing import Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.extract_utils import extract_emergency_info


# Ví dụ sử dụng
async def main():
    # Test với một comment mẫu
    sample_comment = """
    CẦN HỖ TRỢ LƯƠNG THỰC THỰC PHẨM, SẠC, ĐÈN PIN - Tên: chú Tiến - Nhà mình có 2 người già và 2 trẻ nhỏ, đã sắp cạn kiệt đồ ăn thức uống, điện thoại đã sắp cạn pin nên không gọi cứu trợ được. Nhà ở sâu xóm, bị chia cắt ở vùng ngoài, chỉ có người già và trẻ em nên mong đội cứu trợ hỗ trợ. - Địa chỉ: nhà số 9 kiệt 34 An Ninh, phường Kim Long, thành phố Huế (vào sâu trong ngõ có nhà cuối) https://maps.app.goo.gl/nntdfXHne3XNobDp9 Cả xóm nhà mình cũng ở sâu, bị chia cắt xa, nhờ đội cứu trợ hỗ trợ lương thực cho cả xóm luôn ạ - Số điện thoại liên lạc: 0339 186 860 (số của mình đang ở xa, điện thoại người nhà mình đã cạn pin)
    """

    print("Đang trích xuất thông tin từ comment...")
    result = await extract_emergency_info(sample_comment)

    print("\n" + "=" * 60)
    print("KẾT QUẢ TRÍCH XUẤT:")
    print("=" * 60)

    import json

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
