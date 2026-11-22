# app-cuu-ho

Independent development of the rescue application. Source provenance: [ORIGIN.md](ORIGIN.md).


Tổng hợp bài cầu cứu, bóc tách thông tin, đánh giá mức khẩn cấp bằng ba mô hình, định vị và quản lý quá trình xác minh/xử lý.

**Bản đồ dùng Leaflet + OpenStreetMap, không cần Google Cloud Billing hoặc key frontend.** Tìm địa chỉ và đường đi dùng Geoapify tùy chọn; chưa có key vẫn xem bản đồ, AI và nhập tọa độ thủ công được.

## Chạy local

Yêu cầu Python 3.12, uv, Node.js 22+ và Docker Desktop. Tại thư mục gốc:

```powershell
uv sync --frozen
uv run python scripts/setup_demo.py
docker compose up -d postgres
uv run python main.py
```

Terminal khác:

```powershell
cd fe
npm ci
npm run dev -- --host localhost --port 5173 --strictPort
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8099/docs
- Chạy nhanh trên Windows sau khi đã cài dependencies: `powershell -ExecutionPolicy Bypass -File scripts/run_demo.ps1`.
- Đăng nhập bằng `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` trong `.env`. Script setup tạo mật khẩu ngẫu nhiên, không dùng mật khẩu mặc định chung. Startup chỉ tạo tài khoản nếu email đó chưa tồn tại.

## Chạy bằng Docker

```powershell
docker compose up -d --build postgres app frontend
```

Mở http://localhost:8098. API readiness: http://localhost:8091/ready. Các cổng mặc định chỉ bind localhost. Giữ nguyên thư mục `data/postgres`; không chạy các script reset DB hoặc migration reset cũ trên dữ liệu đang dùng.

## API bạn cần lấy sau

Đăng ký gói **Free** tại [Geoapify](https://www.geoapify.com/get-started-with-maps-api/), rồi điền **một key backend**:

```env
# .env ở thư mục gốc
GEOAPIFY_API_KEY=key_cua_ban
GEOCODING_ENABLED=true
```

Khởi động lại backend; với Docker dùng `docker compose up -d --force-recreate --no-deps app` để nạp env mới. Không đặt key này trong `VITE_*`.

Giới hạn mặc định của ứng dụng: geocoding 200/ngày, 4.000/tháng; routing 50/ngày, 1.000/tháng (UTC). Bộ đếm dùng PostgreSQL, có cache và hạn chế 2 lượt/giây toàn nhà cung cấp, không reset khi restart. Khi quota store lỗi, không gửi request ra nhà cung cấp. Tọa độ quá rộng, sai tỉnh hoặc độ khớp thấp cần kiểm tra thủ công. Các Google key cũ không còn được ứng dụng sử dụng.

Nền OSM công cộng chỉ dành cho xem tương tác quy mô nhỏ: giữ attribution, không tải trước hàng loạt/offline. Có thể thay `VITE_MAP_TILE_URL` và `VITE_MAP_ATTRIBUTION` bằng dịch vụ tile riêng khi triển khai lớn hơn.

## Tính năng đã có

- Tìm kiếm địa chỉ không dấu; lọc trạng thái, khẩn cấp, tọa độ, khu vực, thiên tai, thời gian đăng.
- Hiển thị chấm xanh/cam/đỏ theo khẩn cấp thấp/vừa/cao. Điểm AI dùng thang 1/2/3, không phải nguy cơ lũ tại mọi vị trí địa lý.
- Nhập CSV UTF-8 (500 dòng, 3 MB), nhập form, hoặc bóc tách bài thô local rồi kiểm tra trước khi lưu.
- Tác vụ nhập/định vị có tiến độ, hủy, thử lại, lease khôi phục sau khi worker chết; từng bản ghi và cursor commit cùng giao dịch.
- Địa chỉ ghi rõ trong nội dung có thể được khôi phục khi trường location thiếu; trường do người dùng nhập được giữ ưu tiên. Địa chỉ suy ra được đánh dấu cần đối chiếu.
- Ba mô hình Gradient Boosting, Random Forest, LightGBM; bộ prototype hiệu chỉnh xác suất bằng tập calibration riêng rồi lấy trung bình. Chi tiết từng model được lưu theo từng yêu cầu.
- Người xem/ vận hành/ quản trị; phiên HttpOnly, CSRF, hạn chế thử đăng nhập, khóa tài khoản và thu hồi session; audit dùng danh tính đã đăng nhập.
- Sửa thông tin/tọa độ; dữ liệu đầu vào AI thay đổi thì tính lại; chuyển trạng thái có ghi chú. Không tự xác minh dữ liệu crawl.
- Xem báo cáo AI/biểu đồ, xuất CSV, tìm đường từ điểm xuất phát nhập thủ công. Đường đi không phản ánh ngập lụt hay đường bị chặn.

Các dự đoán đã lưu không bị ghi đè chỉ vì thay model. Bộ mới áp dụng khi nhập bài hoặc cập nhật đầu vào AI. Tọa độ/ngày đăng thiếu được giữ rõ trạng thái, không tạo dữ liệu giả.

## Đánh giá mô hình

```powershell
uv run python scripts/train_evaluate.py
```

Tạo model và báo cáo ở `ai/artifacts/prototype/`, giữ nguyên ba model cũ và notebook. Chia nhóm nội dung chuẩn hóa: 309 train, 77 calibration, 97 test; tuning chỉ trên train. Macro F1 kết hợp: khẩn cấp **0,459**, độ tin cậy theo nhãn nguồn **0,810**. Đây là holdout nội bộ, không phải độ chính xác ngoài thực địa; nhãn độ tin cậy chỉ có CAO/THẤP. Xem [model card](docs/MODEL_CARD.md).

## Kiểm thử

```powershell
uv run python -m pytest test/test_model_report.py test/test_prototype.py test/test_operations.py test/test_processing.py test/test_google_geocoding.py test/test_google_maps.py ai/test/test_run_pipeline.py -q
cd fe
npm run lint
npm test
npm run build
npm audit --omit=dev
npx playwright install chromium
cd ..
uv run python scripts/run_e2e.py
```

Test DB dùng schema riêng. E2E chạy API/worker riêng và dọn schema sau khi xong; chặn tải tile ra dịch vụ cộng đồng. Các test Google cũ chỉ kiểm tra hồi quy adapter lịch sử bằng dữ liệu giả lập, không gọi Google thật. Workflow CI đã chuẩn bị trong `.github/workflows/ci.yml`; chưa đẩy mã lên GitHub trong phiên làm việc này.

## Tài liệu

- [Các phase và trạng thái nghiệm thu](docs/PROJECT_PHASES.md)
- [Key, vận hành, backup/restore và kịch bản demo](docs/PROTOTYPE_GUIDE.md)
- [Đánh giá AI và các giới hạn dữ liệu](docs/MODEL_CARD.md)

Phạm vi là prototype demo. Chưa nghiệm thu Geoapify thực tế vì chưa có key, chưa kiểm chứng nhãn bằng chuyên gia, chưa triển khai lên máy chủ Internet.
