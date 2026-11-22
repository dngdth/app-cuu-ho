# Model card — bộ prototype

Mục đích: hỗ trợ sắp xếp yêu cầu cần kiểm tra. Không xác thực sự thật của bài đăng, không dự báo ngập lụt và không tự quyết định điều phối.

## Dữ liệu và cách chia

- 483 dòng trong `crawl/data_clean.csv`, gồm nội dung, thông tin địa điểm, nhu cầu, số người và các cờ đã bóc tách.
- Nhãn khẩn cấp chuẩn hóa: CAO 253, TRUNG BÌNH 159, THẤP 71. Nhãn `confident`: CAO 424, THẤP 59; không có lớp trung bình.
- Nhãn nguồn chưa được kiểm toán chuyên gia. Có thể có dữ liệu cũ, gán nhãn tự động, thiên lệch và các bài cùng một sự kiện.
- Nhóm theo hash của nội dung casefold/chuẩn hóa dấu câu. Không có nội dung trùng chuẩn hóa giữa train/calibration/test. Các bài cùng sự kiện nhưng diễn đạt khác vẫn có khả năng xuất hiện ở nhiều tập.
- Split cố định seed 42: 309 train, 77 calibration, 97 test. Không dùng test để chọn tham số hoặc huấn luyện bộ biến đổi.

## Phương pháp

Ba classifier: Gradient Boosting, Random Forest, LightGBM. Mỗi mục tiêu có encoder/pipeline riêng; các cột label/confident không được đưa vào đặc trưng. Imputer/one-hot chỉ fit trên train. GridSearch nhỏ với StratifiedGroupKFold 3 fold trên train chọn hai cấu hình cho mỗi thuật toán. Sigmoid calibration trên tập 77 dòng riêng, dùng FrozenEstimator giữ nguyên classifier đã học. Kết hợp bằng trung bình các phân bố xác suất đã hiệu chỉnh; không chọn model bằng test.

Các file model cũ và notebook được giữ nguyên. Candidate ở `ai/artifacts/prototype/`; `manifest.json` và `evaluation.json` chứa fingerprint dữ liệu, mã nguồn, artifact và phiên bản. `RESCUE_MODEL_DIR` chọn bộ dùng cho dữ liệu mới. Dự đoán lịch sử không bị ghi đè tự động.

## Kết quả holdout nội bộ

| Bộ dự đoán | Khẩn cấp: macro F1 | Độ tin cậy theo nhãn: macro F1 |
| --- | ---: | ---: |
| Baseline prior/đa số | 0,238 | 0,458 |
| Gradient Boosting đã hiệu chỉnh | 0,422 | 0,810 |
| Random Forest đã hiệu chỉnh | 0,491 | 0,810 |
| LightGBM đã hiệu chỉnh | 0,408 | 0,810 |
| Trung bình ba mô hình | 0,459 | 0,810 |

Macro F1 không phải tỷ lệ dự đoán đúng. Ensemble hiện chưa vượt Random Forest về macro F1 khẩn cấp. Không chọn lại phương pháp theo kết quả test; cần tập mới để xác nhận cải tiến. Khẩn cấp có hiệu năng còn hạn chế, cần người vận hành đối chiếu.

Ma trận nhầm lẫn, precision/recall từng lớp, log loss trước/sau calibration, best params và điểm CV nằm trong `evaluation.json`. PNG biểu đồ nằm cạnh file. Permutation importance được tính post-hoc trên test cho Gradient Boosting, không dùng chọn đặc trưng/tham số; không diễn giải như quan hệ nhân quả hoặc giải thích cá nhân của từng bài.

## Giới hạn và bước tiếp theo

1. Có tập nhãn do người có chuyên môn xác minh, tách theo thời gian/sự kiện và nguồn bài.
2. Thu thập đủ ví dụ độ tin cậy thấp/trung bình; định nghĩa rõ tiêu chí nhãn.
3. Đánh giá recall lớp khẩn cấp cao và kiểm tra các false negative, theo dõi drift.
4. Đánh giá calibration trên tập ngoài trước khi coi xác suất là thước đo tin cậy thực tế.

Tái tạo: `uv run python scripts/train_evaluate.py`. Script chỉ ghi candidate/report, không sửa CSV, model gốc hay notebook.
