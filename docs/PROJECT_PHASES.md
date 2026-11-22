# Các phase — cập nhật 22/11/2026

Mục tiêu đã đổi sang prototype đi thi, không yêu cầu Google Cloud Billing. Phần code của cả sáu phase đã triển khai; phần cần key thật hoặc môi trường ngoài được tách rõ bên dưới.

| Phase | Kết quả trong repo | Trạng thái |
| --- | --- | --- |
| 1. Dữ liệu/API | Cập nhật PostGIS đúng cột, nearby, trạng thái có quy tắc, khu vực, thống kê và lịch sử | Đã có và kiểm thử |
| 2. Màn hình kiểm tra | Bộ lọc, sửa địa chỉ/tọa độ, xác minh có ghi chú, lịch sử, báo cáo tổng quan | Đã có và kiểm thử E2E |
| 3. Bản đồ/định vị | Leaflet/OSM, adapter Geoapify, kiểm tra độ chính xác, cache/quota bền vững, đường đi; link Google nguồn vẫn đọc được | Code và mock tests xong; chờ key để nghiệm thu dữ liệu thật |
| 4. AI/đầu vào | Bóc tách local, phục hồi địa chỉ rõ trong nội dung, nguồn/ngày thu thập, train/calibration/test theo nhóm, tuning, báo cáo và biểu đồ | Đã chạy trên 483 dòng; còn giới hạn chất lượng nhãn, xem MODEL_CARD |
| 5. Tài khoản/vận hành | Ba vai trò, HttpOnly session/CSRF, audit danh tính, khóa tài khoản, hàng đợi Postgres có lease/cursor/retry/cancel, quota API và readiness | Đã có, integration tests/E2E qua |
| 6. Kiểm thử/đóng gói | Unit/integration/E2E, lint/build/audit, Docker FE+BE, CI, backup/restore sang DB mới, hướng dẫn demo | Docker build/chạy local, E2E và restore đã thực hiện; CI mới chuẩn bị, chưa chạy trên GitHub |

## Nghiệm thu prototype

Đã kiểm tra tại local: 92 test backend, 5 test logic frontend, 3 E2E trên bản build production; lint/build và npm audit runtime qua. Docker FE/BE đã build/chạy thử; backup/restore đã đếm đủ 486 yêu cầu. Workflow CI chưa được chạy trên GitHub trong phiên này.

1. Mở `http://localhost:5173` (Vite) hoặc `http://localhost:8098` (Docker). Bản đồ chạy không cần key frontend.
2. Đăng nhập bằng admin local trong `.env`; có thể tạo tài khoản viewer/operator trong “Tài khoản”.
3. “Bóc tách bài viết”: dán một bài có `Địa chỉ: ...`, kiểm tra form, xếp hàng nhập. Đóng hộp thoại vẫn theo dõi được tác vụ.
4. Tìm bài vừa nhập, mở “Kiểm tra / cập nhật”; nhập tọa độ, ghi căn cứ, chuyển Chưa xác minh → Chờ xử lý. Kiểm tra lịch sử có tài khoản thật.
5. Bấm “Đánh giá mô hình” để xem baseline, từng model, ensemble, các biểu đồ và giới hạn nhãn.
6. Sau khi có `GEOAPIFY_API_KEY`, restart backend rồi định vị một bài trước khi chạy lô 20 bài; đối chiếu vị trí nhà thực tế. Thử đường đi bằng điểm xuất phát thủ công.

Trạng thái: `unverified → pending → in_progress → resolved`; có nhánh rejected và mở lại theo quy tắc trong `app/core/workflow.py`. Không xác minh hàng loạt dữ liệu cũ.

## Dữ liệu được giữ

- 486 yêu cầu cũ; 167 có tọa độ và 319 thiếu tọa độ tại thời điểm đổi nhà cung cấp.
- Không xóa nguồn, không thay dự đoán/tọa độ cũ trong quá trình triển khai các phase sau.
- Model mới không tự chạy lại trên dữ liệu lịch sử; phiên bản/phương pháp được lưu khi xử lý mới. Các bản ghi cũ vẫn giữ kết quả đã lưu.
- Bảng account/session/job/cache/quota được thêm độc lập. Không chạy lại migration reset cũ.
- Backup đã tạo và thử restore đủ 486 yêu cầu sang `rescue_restore_phase6_20261122`, không ghi đè DB chính.

## Phần chưa thể khẳng định hoàn tất thực tế

- Tỷ lệ định vị chính xác của Geoapify với địa chỉ Việt Nam: cần key và tập mẫu đối chiếu.
- Chất lượng AI trên tập ngoài hoặc dữ liệu đã xác minh: cần nhãn độc lập; macro F1 hiện tại không phải chứng nhận vận hành cứu hộ.
- CI trên GitHub và triển khai Internet/TLS: code/config đã có nhưng chưa thực thi trên tài khoản/máy chủ bên ngoài.
