# Kiểm soát chi phí Google cho bản prototype

> Tài liệu lịch sử của phương án Google. Từ 22/11/2026, ứng dụng dùng Leaflet/OSM + Geoapify và không đọc các biến Google để định vị/hiển thị. Xem [hướng dẫn mới](PROTOTYPE_GUIDE.md); không làm các bước bật Google bên dưới cho bản hiện tại.

## Trạng thái local

Ứng dụng mặc định không tải Google Maps SDK và không gọi Google Geocoding/Places, kể cả khi có key:

```env
# .env backend
GOOGLE_MAPS_ENABLED=false

# fe/.env.local frontend
VITE_GOOGLE_MAPS_ENABLED=false
```

Danh sách, điểm AI, cập nhật thủ công và tọa độ lưu trong DB vẫn dùng được. Các link Google Maps nguồn có thể được phân giải như trước; đây không phải lời gọi Geocoding/Places có key.

Đây là công tắc trong ứng dụng, không phải thay đổi quota Google Cloud. Nó không chặn việc dùng key ngoài ứng dụng và không xóa chi phí đã phát sinh.

## Thiết lập Cloud trước khi bật lại

1. Chọn project `rescue-map-demo` và mở Google Maps Platform → Quotas (hoặc APIs & Services → API tương ứng → Quotas & System Limits).
2. Với Geocoding, nếu có quota Requests/Queries per day, đặt 100/ngày. Theo đơn vị đó, tối đa 3.100 lượt/tháng 31 ngày, thấp hơn hạn mức miễn phí hiện tại 10.000. Hạn mức miễn phí cộng gộp trên tài khoản billing; phải tính cả project khác cùng dùng dịch vụ.
3. Với Places API (New), xem quota cho phương thức Text Search. Nếu tài khoản có quota theo ngày phù hợp, đặt 50/ngày (tối đa 1.550/tháng, dưới 5.000 Text Search Pro hiện tại). Nếu chỉ có quota theo phút, nó chỉ hạn chế tốc độ; không coi đó là khóa chi phí tháng. Giữ Places tắt khi chưa có giới hạn tổng lượt phù hợp.
4. Với Maps JavaScript API, kiểm tra quota tải bản đồ. Tài liệu hiện liệt kê giới hạn theo phút; không giả định tài khoản có quota theo ngày. Giữ công tắc frontend tắt nếu chưa xác minh được cách giới hạn phù hợp.
5. Giữ key frontend giới hạn đúng website và Maps JavaScript API; key backend chỉ Geocoding/Places. Khi triển khai, giới hạn backend theo IP máy chủ nếu có IP ổn định.
6. Kiểm tra Billing → Reports/Cost table để xem chi phí đã có. Có thể bật cảnh báo ngân sách, nhưng cảnh báo không tự ngắt dịch vụ và dữ liệu billing có độ trễ.

Không bảo đảm “không trừ tiền” chỉ bằng một budget, quota theo phút hoặc công tắc frontend. Nếu yêu cầu tuyệt đối không có khả năng phát sinh chi phí Google mới, tiếp tục để hai công tắc tắt và tắt các API trên Cloud khi không cần; dữ liệu demo có thể dùng tọa độ tự nhập/nguồn được phép và nhà cung cấp bản đồ phù hợp khác sau khi đánh giá riêng.

Chỉ đổi công tắc tương ứng sang `true` và khởi động lại dịch vụ sau khi người dùng đã kiểm tra quota. Không bật tự động hoặc chạy backfill để thử quota.

Tài liệu chính thức đã kiểm tra ngày 21/11/2026:

- [Kiểm soát chi phí và quota](https://developers.google.com/maps/billing-and-pricing/manage-costs)
- [Geocoding: quota và billing](https://developers.google.com/maps/documentation/geocoding/usage-and-billing)
- [Maps JavaScript: quota tải bản đồ](https://developers.google.com/maps/documentation/javascript/usage-and-billing#map_load_quotas)
- [Places API: giới hạn theo phương thức](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing#usage_limits)
- [Bảng giá và hạn mức miễn phí](https://developers.google.com/maps/billing-and-pricing/pricing)
