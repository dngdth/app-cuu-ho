import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Tests never fetch or pre-seed community map tiles.
  await page.route('https://tile.openstreetmap.org/**', (route) => route.abort());
  await page.goto('/');
});

async function login(page) {
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel(/^Email/).fill('e2e@example.test');
  await dialog.getByLabel(/^Mật khẩu/).fill('E2E-only-password-2026');
  await dialog.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.getByText('E2E Operator · Quản trị')).toBeVisible();
}

test('anonymous visitors can view map/data but cannot edit', async ({ page }) => {
  await expect(page.getByRole('heading', { name: /^Điểm demo E2E/ })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Bản đồ các yêu cầu cứu hộ' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Đăng nhập để cập nhật' })).toBeDisabled();
  await page.getByRole('button', { name: 'Đánh giá mô hình' }).click();
  await expect(page.getByRole('dialog').getByText('Macro F1', { exact: true }).first()).toBeVisible();
});

test('login, extract raw post, queue import, review a coordinate/status and read audit', async ({ page }) => {
  await login(page);
  await page.getByRole('button', { name: 'Nhập dữ liệu và đánh giá AI' }).click();
  let dialog = page.getByRole('dialog');
  await dialog.getByRole('tab', { name: 'Bóc tách bài viết' }).click();
  await dialog.getByLabel('Dán nguyên bài viết nguồn').fill('E2E luồng hoàn chỉnh: Có 3 người cần cứu hộ. Địa chỉ: 10/82 Đào Duy Anh, Phú Xuân, Thành phố Huế');
  await dialog.getByRole('button', { name: 'Bóc tách và kiểm tra' }).click();
  await expect(dialog.getByLabel('Địa chỉ', { exact: true })).toHaveValue('10/82 Đào Duy Anh, Phú Xuân, Thành phố Huế');
  await dialog.getByRole('button', { name: 'Đánh giá và lưu', exact: true }).click();
  await expect(dialog.getByText(/Đã xếp hàng tác vụ/)).toBeVisible();
  await dialog.getByRole('button', { name: 'Đóng', exact: true }).click();
  await expect(page.getByText(/Nhập dữ liệu · Hoàn tất/)).toBeVisible({ timeout: 30000 });
  await page.getByPlaceholder('Tìm kiếm địa điểm, khu vực...').fill('E2E luồng hoàn chỉnh');
  await expect(page.getByRole('button', { name: 'Kiểm tra / cập nhật', exact: true })).toHaveCount(1);
  await page.getByRole('button', { name: 'Kiểm tra / cập nhật', exact: true }).click();
  dialog = page.getByRole('dialog');
  await dialog.getByLabel('Vĩ độ (latitude)', { exact: true }).fill('16.47');
  await dialog.getByLabel('Kinh độ (longitude)', { exact: true }).fill('107.57');
  await dialog.getByLabel('Trạng thái', { exact: true }).click();
  await page.getByRole('option', { name: 'Đã xác minh · Chờ xử lý', exact: true }).click();
  await dialog.getByLabel('Căn cứ kiểm tra / lý do thay đổi').fill('E2E: đã đối chiếu vị trí và xác minh nguồn');
  await dialog.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await page.getByRole('button', { name: 'Kiểm tra / cập nhật', exact: true }).click();
  dialog = page.getByRole('dialog');
  await dialog.getByRole('tab', { name: 'Lịch sử thay đổi' }).click();
  await expect(dialog.getByText('E2E: đã đối chiếu vị trí và xác minh nguồn')).toBeVisible();
  await expect(dialog.getByText(/E2E Operator \(e2e@example.test\)/)).toBeVisible();
});

test('concurrent imports of the same post create only one request', async ({ page }) => {
  await login(page);
  const session = await (await page.request.get('/api/auth/me')).json();
  const data = { records: [{ content: 'E2E concurrent duplicate', location: 'Huế', affected_people: 3,
    coordinate: { type: 'Point', coordinates: [107.58, 16.46] } }], geocode: false };
  const responses = await Promise.all([1, 2].map(() => page.request.post('/api/processing/import', {
    data, headers: { 'X-CSRF-Token': session.csrf_token },
  })));
  for (const response of responses) expect(response.status()).toBe(200);
  const results = await Promise.all(responses.map((response) => response.json()));
  expect(results.reduce((sum, result) => sum + result.created, 0)).toBe(1);
  expect(results.reduce((sum, result) => sum + result.duplicates, 0)).toBe(1);
});
