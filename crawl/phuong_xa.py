import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def crawl_wards_with_parent():
    url = input("Nhập URL trang web: ").strip()
    parent_id = input("Nhập parent_id (ID của tỉnh/thành phố): ").strip()
    
    # Giả lập trình duyệt để tránh bị chặn
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        print("Đang tải dữ liệu từ website...")
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Kiểm tra lỗi kết nối
        response.encoding = 'utf-8' # Đảm bảo đọc đúng tiếng Việt

        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm bảng chứa dữ liệu (thường nằm trong thẻ table)
        tables = soup.find_all('table')
        
        print(f"Tìm thấy {len(tables)} bảng trên trang web")
        
        if not tables:
            print("Không tìm thấy bảng dữ liệu trên trang web.")
            return
        
        # Thử từng bảng để tìm bảng đúng (bảng có nhiều dòng nhất)
        table = None
        max_rows = 0
        selected_idx = -1
        
        for idx, t in enumerate(tables):
            rows = t.find_all('tr')
            print(f"Bảng {idx + 1}: có {len(rows)} dòng")
            
            if len(rows) > 0:
                first_row = rows[0].find_all(['td', 'th'])
                print(f"  Dòng đầu có {len(first_row)} cột")
                
                # Kiểm tra xem có phải bảng danh sách xã/phường không
                # Bảng phải có ít nhất 2 cột và nhiều hơn 5 dòng
                if len(first_row) >= 2 and len(rows) > 5:
                    # Kiểm tra header có chứa "xã" hoặc "phường" hoặc "STT"
                    header_text = ' '.join([cell.get_text(strip=True).lower() for cell in first_row])
                    if 'xã' in header_text or 'phường' in header_text or 'stt' in header_text or 'số' in header_text:
                        if len(rows) > max_rows:
                            max_rows = len(rows)
                            table = t
                            selected_idx = idx + 1
        
        if not table:
            print("\nKhông tìm thấy bảng phù hợp (cần bảng có >5 dòng và chứa header STT/xã/phường).")
            return
        
        print(f"\n=> Chọn bảng {selected_idx} (có {max_rows} dòng)")

        rows = table.find_all('tr')
        
        # Xác định số cột của bảng và phát hiện cột chứa tên mới
        num_cols = 0
        name_col_index = 1  # Mặc định
        
        if len(rows) > 0:
            header_row = rows[0].find_all(['td', 'th'])
            num_cols = len(header_row)
            
            # Debug: in header
            print(f"\nHeader bảng:")
            for idx, col in enumerate(header_row):
                col_text = col.get_text(strip=True)
                print(f"  Cột {idx}: '{col_text}'")
            
            # Tìm cột chứa tên - theo thứ tự ưu tiên:
            # 1. "Tên đơn vị hành chính"
            # 2. "sau sắp nhập", "sau sáp nhập", "sau sắp xếp"
            # 3. "mới" (không có "trước")
            found = False
            
            for idx, col in enumerate(header_row):
                col_text = col.get_text(strip=True).lower()
                
                # Ưu tiên 1: Tên đơn vị hành chính
                if 'tên đơn vị' in col_text or 'ten don vi' in col_text:
                    name_col_index = idx
                    print(f"\n✓ Tìm thấy cột 'Tên đơn vị hành chính' tại cột {idx}")
                    found = True
                    break
                
                # Ưu tiên 2: Sau sắp nhập/xếp
                if any(keyword in col_text for keyword in ['sau sắp nhập', 'sau sáp nhập', 'sau sắp xếp', 'sau sap nhap']):
                    name_col_index = idx
                    print(f"\n✓ Tìm thấy cột 'sau sắp nhập/xếp' tại cột {idx}: '{col.get_text(strip=True)}'")
                    found = True
                    break
            
            # Ưu tiên 3: Mới (không có "trước")
            if not found:
                for idx, col in enumerate(header_row):
                    col_text = col.get_text(strip=True).lower()
                    if 'mới' in col_text and 'trước' not in col_text:
                        name_col_index = idx
                        print(f"\n✓ Tìm thấy cột 'mới' tại cột {idx}: '{col.get_text(strip=True)}'")
                        found = True
                        break
            
            if not found:
                print(f"\n⚠ Không tìm thấy cột phù hợp, sử dụng mặc định cột {name_col_index}")
        
        print(f"\nBảng có {num_cols} cột")
        print(f"Sẽ lấy dữ liệu từ cột {name_col_index}")
        
        data = []
        # Duyệt qua từng dòng trong bảng
        print(f"\nBắt đầu xử lý {len(rows)} dòng...")
        
        # In ra dòng đầu tiên để debug
        if len(rows) > 0:
            print("\n=== DEBUG: Dòng đầu tiên ===")
            first_cols = rows[0].find_all(['td', 'th'])
            for i, col in enumerate(first_cols):
                print(f"Cột {i}: '{col.get_text(strip=True)}'")
        
        # Tìm dòng tiêu đề (header) và bỏ qua
        start_idx = 0
        for idx, row in enumerate(rows):
            cols = row.find_all(['td', 'th'])
            if len(cols) > 0:
                first_col_text = cols[0].get_text(strip=True).lower()
                if 'stt' in first_col_text or 'số tt' in first_col_text:
                    start_idx = idx + 1
                    print(f"Tìm thấy dòng tiêu đề tại dòng {idx}, bắt đầu đọc từ dòng {start_idx}")
                    break
        
        for idx in range(start_idx, len(rows)):
            row = rows[idx]
            cols = row.find_all(['td', 'th'])
            
            # Debug: in ra 3 dòng đầu
            if idx < start_idx + 3:
                print(f"\n--- Dòng {idx} có {len(cols)} cột ---")
                for i, col in enumerate(cols):
                    print(f"  Cột {i}: '{col.get_text(strip=True)}'")
            
            if len(cols) > name_col_index:
                # Lấy tên từ cột đã xác định
                ten_xa_moi = cols[name_col_index].get_text(strip=True)
                
                # Bỏ qua dòng trống
                if ten_xa_moi and len(ten_xa_moi) > 0:
                    data.append({
                        "parent_id": parent_id,
                        "name": ten_xa_moi
                    })
                    if idx < start_idx + 3:
                        print(f"  → Thêm: parent_id={parent_id}, name='{ten_xa_moi}'")

        # Chuyển dữ liệu vào DataFrame của Pandas
        df = pd.DataFrame(data)

        # Xử lý trường hợp có thể bị trùng do gộp ô
        df = df.drop_duplicates()
        
        print(f"\nĐã crawl được {len(df)} xã/phường")
        print("\nPreview 5 dòng đầu:")
        print(df.head())

        # Ghi nối vào file CSV
        output_file = "danh_sach_phuong_xa.csv"
        
        try:
            # Kiểm tra xem file đã tồn tại chưa
            if os.path.exists(output_file):
                # Nối vào file cũ (append mode, không ghi header)
                df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8-sig')
                print(f"\n✓ Thành công! Đã nối thêm {len(df)} xã/phường vào file: {output_file}")
            else:
                # Tạo file mới với header
                df.to_csv(output_file, mode='w', header=True, index=False, encoding='utf-8-sig')
                print(f"\n✓ Thành công! Đã tạo file mới với {len(df)} xã/phường: {output_file}")
        except PermissionError:
            # Nếu file đang mở, tạo file mới với timestamp
            import time
            output_file = f"danh_sach_phuong_xa_{int(time.time())}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n⚠ File cũ đang mở. Đã lưu vào file mới: {output_file}")

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    crawl_wards_with_parent()