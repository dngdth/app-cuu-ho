# Hướng dẫn chạy và trình diễn prototype

## Tài khoản

`scripts/setup_demo.py` chỉ điền cấu hình còn thiếu và sinh `INITIAL_ADMIN_PASSWORD` ngẫu nhiên trong `.env`; không in key/password ra log. Startup tạo admin nếu email chưa tồn tại. Tài khoản viewer chỉ xem, operator nhập/xác minh/định vị, admin tạo/khóa người dùng và có quyền quản trị danh mục/xóa bản ghi qua API.

Thay `INITIAL_ADMIN_PASSWORD` trong file không tự đổi mật khẩu tài khoản đã tồn tại. Nếu quên, chạy tại máy có quyền DB:

```powershell
uv run python scripts/manage_users.py --email admin@rescue.local
```

Mật khẩu được nhập ẩn. Phiên cũ bị thu hồi. Khi triển khai qua HTTPS, đặt `AUTH_COOKIE_SECURE=true` và cấu hình `ALLOWED_ORIGINS` đúng domain của bạn; không dùng `*`.

API ghi dữ liệu cần session cookie và `X-CSRF-Token`. Login trả csrf_token; `/auth/me` khôi phục token cho phiên đang dùng. Python `clients.RescueAPIClient.login(email, password)` chia sẻ session cho các resource client.

CLI nhập CSV:

```powershell
uv run python scripts/import_rescue_data.py crawl/data_clean.csv --email admin@rescue.local --no-geocode
```

CLI sẽ hỏi mật khẩu ẩn. Mặc định nên nhập không định vị trước; dùng giao diện/tác vụ định vị sau khi đối chiếu nguồn.

## Geoapify key duy nhất

1. Vào [Geoapify — đăng ký và lấy key](https://www.geoapify.com/get-started-with-maps-api/), chọn **Free**, tạo project và lấy key. Không cần Google Cloud Billing.
2. Điền `GEOAPIFY_API_KEY` trong `.env` gốc, giữ `GEOCODING_ENABLED=true`.
3. Restart backend. Với Docker cần recreate container để nạp env: `docker compose up -d --force-recreate --no-deps app`.
4. Đăng nhập, thử một bài hoặc dùng Swagger gọi `/geocode/forward` bằng session operator. Chỉ chấp nhận điểm nhà/địa điểm khớp địa chỉ; kết quả tâm đường/khu vực hoặc thiếu tin cậy cần nhập tay.
5. Key chỉ nằm ở backend. Frontend không cần key, dùng tile OSM mặc định. Muốn đổi tile thì chỉnh `VITE_MAP_TILE_URL`, `VITE_MAP_ATTRIBUTION` và build/restart frontend.

Địa chỉ có số nhà được thử nguyên văn, sau đó tách riêng số nhà/ngõ/kiệt, tên đường và tỉnh/thành đã ghi rõ; tối đa hai truy vấn cho mỗi lần xử lý. Geoapify có thể trả nhãn `building` và lặp lại số nhà đã hỏi dù tọa độ chỉ đại diện tuyến đường (`confidence_building_level=0`). Những kết quả này được lưu dưới dạng **Gợi ý tuyến đường**, không đưa vào tọa độ chính thức của yêu cầu. Mở **Kiểm tra / cập nhật → Mở vị trí gợi ý trên bản đồ**, đối chiếu và nhập tọa độ nhà đã xác nhận. Gợi ý có hạn lưu tạm 29 ngày và được dọn cùng dữ liệu geocoding khác.

Free Geoapify hiện cung cấp 3.000 credits/ngày, các project chung tài khoản chia sẻ quota; không tự chuyển thành thuê bao trả phí. Hạn mức ứng dụng nhỏ hơn mức này để phục vụ demo. Xem [chính sách nhà cung cấp](https://www.geoapify.com/get-started-with-maps-api/) và [giá hiện tại](https://www.geoapify.com/pricing/).

Không dùng public Nominatim cho lô crawl hoặc public OSRM cho demo có dữ liệu nhạy cảm. Hệ thống không gửi bài viết đầy đủ/số điện thoại sang Geoapify; chỉ gửi địa chỉ hoặc tọa độ cần định vị/tìm đường.

## Giới hạn và cache

| Chức năng | Ngày | Tháng |
| --- | ---: | ---: |
| Geocoding | 200 | 4.000 |
| Routing | 50 | 1.000 |

Bộ đếm UTC được reserve trong PostgreSQL **trước** HTTP, giới hạn tổng 2 calls/giây qua advisory lock. Đếm bảo thủ cả cuộc gọi lỗi; cache hit không tiêu lượt mới. Cache geocoding 1 ngày, đường đi 1 giờ; vị trí có hạn lưu tạm 29 ngày và được dọn theo lịch. Khi store lỗi, ngừng gọi ra ngoài. Không có retry HTTP vô hạn, tối đa hai dạng địa chỉ cho mỗi lần tra cứu.

Không reset bộ đếm bằng cách đổi key hoặc restart. Giới hạn này chỉ bao phủ cuộc gọi qua ứng dụng; nếu dùng cùng key/tài khoản ở ứng dụng khác cần tính cả phần đó. Nền OSM không đi qua bộ đếm Geoapify: chỉ tải tile người dùng đang xem, giữ cache trình duyệt và attribution, không có chức năng tải trước/offline. [Chính sách OSM](https://operations.osmfoundation.org/policies/tiles/).

## Tác vụ và vận hành

- Job nhập: tối đa 500 dòng/3 MB, tối đa 3 job đang chờ/chạy mỗi tài khoản. Ngày thu thập tương đối chỉ được quy đổi khi có mốc thật.
- Worker chạy trong backend, claim bằng `SKIP LOCKED`, lease 180 giây. Bản ghi và cursor commit cùng giao dịch. Tác vụ lỗi bất ngờ thử tối đa ba lần; thiếu key/quota thì blocked, có nút thử lại.
- Chọn một cách chạy backend cho demo (native hoặc Docker). Nếu chạy nhiều instance chung DB, chúng phải có cùng key/hạn mức/model/config; sau khi đổi env cần restart tất cả instance để tránh worker dùng cấu hình cũ.
- Hủy dừng từ bản ghi tiếp theo; các bản ghi đã commit vẫn giữ. Khóa tài khoản cũng dừng tác vụ của tài khoản đó.
- Job hoàn tất/hủy xóa payload nguồn khỏi job; lịch sử tác vụ hoàn tất/lỗi được dọn sau 7 ngày. Không xóa nguồn đã nhập vào rescue_request.
- Xem tiến độ/hạn mức ở giao diện, hoặc `/jobs`, `/geocode/usage`. `/health` kiểm tra tiến trình; `/ready` kiểm tra DB và sự hiện diện ba artifact model.
- Logs local: `.backend.stderr.log`, `.backend.stdout.log`. Docker: `docker compose logs --tail 100 app`. Không chia sẻ `.env`, file backup hoặc log chứa dữ liệu cá nhân.

## Backup/restore

```powershell
uv run python scripts/backup_db.py backup
uv run python scripts/backup_db.py restore --file backups/ten-ban-sao.dump --target-db rescue_restore_demo
```

Backup binary `.dump` nằm trong `backups/` đã gitignore. Restore bắt buộc database mới, từ chối tên DB nguồn và không dùng `--clean`/ghi đè. Sau restore script đếm số rescue_request. Bản diễn tập hiện có: `backups/prototype-phase6.dump` → `rescue_restore_phase6_20261122` (486 yêu cầu). Database này được giữ riêng để kiểm tra, không được chọn làm DB ứng dụng.

## Kịch bản demo 5 phút

1. Mở bản đồ, giải thích chấm thể hiện khẩn cấp của từng yêu cầu, không phải bản đồ dự báo lũ tổng quát.
2. Tìm `dao duy anh`, lọc chưa định vị/chưa xác minh. Cho thấy giữ được dữ liệu thiếu thay vì tạo điểm giả.
3. Đăng nhập, dán bài mẫu vào “Bóc tách bài viết”, đối chiếu địa chỉ/số người, xếp hàng nhập. Quan sát tác vụ.
4. Thêm tọa độ đã kiểm tra, xác minh có căn cứ, xem lịch sử và marker cập nhật.
5. Mở báo cáo AI: nêu tập test riêng, baseline, macro F1, dữ liệu chưa được gán nhãn chuyên gia. Nếu chưa có key, demo nhập tay; không trình bày mock geocoding như kết quả thật.

## Triển khai ngoài máy local

Docker đã chạy local với cổng 8098/8091 chỉ trên loopback. Để lên máy chủ, cần domain/HTTPS reverse proxy, cookie Secure, ALLOWED_ORIGINS cụ thể, mật khẩu DB/admin riêng và backup ngoài ổ hệ thống. Không mở cổng DB ra Internet. Prototype đang cho xem danh sách công khai; dùng dữ liệu demo đã ẩn danh khi trình diễn công khai. Không coi cấu hình local là nghiệm thu production.
