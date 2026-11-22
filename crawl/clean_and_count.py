"""
Làm sạch dữ liệu CSV:
1. Tách những dòng có nhiều tên (ngăn cách bởi dấu phẩy, "và") thành nhiều dòng riêng
2. Đếm số lượng theo parent_id
"""
import pandas as pd
import re

def split_names(name_str):
    """
    Tách chuỗi chứa nhiều tên thành list các tên riêng
    Ví dụ: "Minh Khai, Hoàng Văn Thụ và Phan Bội Châu" -> ["Minh Khai", "Hoàng Văn Thụ", "Phan Bội Châu"]
    """
    # Loại bỏ các cụm từ mô tả (một phần, phần còn lại...)
    name_str = re.sub(r'\(.*?\)', '', name_str)  # Loại bỏ nội dung trong ngoặc
    name_str = re.sub(r'một phần\s+', '', name_str, flags=re.IGNORECASE)
    name_str = re.sub(r'phần còn lại\s+', '', name_str, flags=re.IGNORECASE)
    name_str = re.sub(r'sau khi sáp nhập.*', '', name_str, flags=re.IGNORECASE)
    
    # Thay thế "và" bằng dấu phẩy để dễ split
    name_str = re.sub(r'\s+và\s+', ', ', name_str)
    
    # Split theo dấu phẩy
    names = [n.strip() for n in name_str.split(',')]
    
    # Loại bỏ tên trống hoặc quá ngắn
    names = [n for n in names if len(n) > 2]
    
    return names

def clean_csv(input_file, output_file):
    """
    Đọc CSV, tách các tên, và lưu kết quả
    """
    print(f"Đọc file: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    print(f"Tổng số dòng ban đầu: {len(df)}")
    
    # Lưu dữ liệu gốc để so sánh
    original_count_by_parent = df.groupby('parent_id').size()
    
    print("\nSố lượng theo parent_id (ban đầu):")
    for parent_id, count in original_count_by_parent.items():
        if parent_id != '':  # Bỏ qua tỉnh (parent_id rỗng)
            print(f"  Parent {parent_id}: {count} dòng")
    
    # Tách các tên
    new_rows = []
    
    for idx, row in df.iterrows():
        name = row['name']
        parent_id = row['parent_id']
        
        # Kiểm tra xem có nhiều tên không (có dấu phẩy hoặc "và")
        if ',' in name or ' và ' in name.lower():
            # Tách thành nhiều tên
            names = split_names(name)
            
            if len(names) > 1:
                print(f"\nDòng {idx}: Tách '{name[:50]}...' thành {len(names)} tên")
                for n in names:
                    print(f"  - {n}")
                
                # Thêm từng tên như một dòng riêng
                for n in names:
                    new_rows.append({
                        'parent_id': parent_id,
                        'name': n
                    })
            else:
                # Không tách được, giữ nguyên
                new_rows.append(row.to_dict())
        else:
            # Không có dấu phẩy/và, giữ nguyên
            new_rows.append(row.to_dict())
    
    # Tạo DataFrame mới
    df_new = pd.DataFrame(new_rows)
    
    # Loại bỏ trùng lặp
    before_dedup = len(df_new)
    df_new = df_new.drop_duplicates()
    after_dedup = len(df_new)
    
    if before_dedup > after_dedup:
        print(f"\n✓ Đã loại bỏ {before_dedup - after_dedup} dòng trùng lặp")
    
    print(f"\nTổng số dòng sau khi xử lý: {len(df_new)}")
    
    # Đếm theo parent_id
    new_count_by_parent = df_new.groupby('parent_id').size()
    
    print("\nSố lượng theo parent_id (sau xử lý):")
    for parent_id, count in new_count_by_parent.items():
        if parent_id != '':
            original = original_count_by_parent.get(parent_id, 0)
            diff = count - original
            print(f"  Parent {parent_id}: {count} dòng (thay đổi: {diff:+d})")
    
    # Lưu file
    df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ Đã lưu vào: {output_file}")
    
    # Tạo file thống kê
    stats_file = output_file.replace('.csv', '_stats.txt')
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("=== THỐNG KÊ SỐ LƯỢNG THEO PARENT_ID ===\n\n")
        
        for parent_id, count in sorted(new_count_by_parent.items()):
            if parent_id != '':
                f.write(f"Parent ID {parent_id}: {count} xã/phường\n")
        
        f.write(f"\nTổng cộng: {len(df_new[df_new['parent_id'] != ''])} xã/phường\n")
    
    print(f"✓ Đã lưu thống kê vào: {stats_file}")

if __name__ == "__main__":
    input_file = "danh_sach_phuong_xa.csv"
    output_file = "danh_sach_phuong_xa_cleaned.csv"
    
    print("=== LÀM SẠCH VÀ ĐẾM DỮ LIỆU ===\n")
    
    clean_csv(input_file, output_file)
    
    print("\n✓ Hoàn tất!")
