import { test, expect } from '@playwright/test';

const origin = [107.58, 16.46];
const requests = [7, 3, 6, 1, 5, 2, 4].map((index) => ({ id: 1000 + index,
  title: `Địa điểm thử ${index}`, location: `Địa chỉ thử ${index}`, status: 'unverified', urgency_score: 2,
  coordinate: { type: 'Point', coordinates: [origin[0], origin[1] + index * 0.01] }, needs: [], disaster_types: [] }));

test('one shared Maps link finds five unique nearest destinations and five independent routes', async ({ page }) => {
  await page.route('https://tile.openstreetmap.org/**', (route) => route.abort());
  await page.route('**/api/auth/me', (route) => route.fulfill({ json: {
    user: { id: 1, name: 'Vận hành thử', role: 'operator' }, csrf_token: 'test-csrf',
  } }));
  await page.route('**/api/jobs', (route) => route.fulfill({ json: [] }));
  await page.route('**/api/geocode/status', (route) => route.fulfill({ json: { configured: true } }));
  await page.route('**/api/rescue_request/**', (route) => route.fulfill({ json: [
    ...requests, { ...requests.find((row) => row.id === 1001), id: 2001, title: 'Trùng địa điểm' },
    { ...requests[0], id: 3001, coordinate: null },
  ] }));
  const resolvedLinks = [], routeRequests = [];
  await page.route('**/api/geocode/resolve-link', (route) => {
    resolvedLinks.push(route.request().postDataJSON().url);
    return route.fulfill({ json: { coordinate: { type: 'Point', coordinates: origin } } });
  });
  await page.route('**/api/geocode/route', (route) => {
    const data = route.request().postDataJSON();
    routeRequests.push(data);
    if (routeRequests.length === 2) return route.fulfill({ status: 502, json: { detail: 'Kết nối thử bị gián đoạn.' } });
    return route.fulfill({ json: { geometry: { type: 'LineString', coordinates: [data.start.coordinates, data.end.coordinates] },
      distance_m: 1500, duration_s: 300 } });
  });
  await page.goto('/');
  await expect(page.getByText('Vận hành thử · Vận hành')).toBeVisible();
  await expect(page.getByText(/Hiển thị 9 \/ 9 yêu cầu/)).toBeVisible();
  const panel = page.getByRole('region', { name: 'Tìm đường tới các địa điểm thiên tai' });
  await panel.getByLabel('Link Google Maps vị trí hiện tại').fill('https://maps.app.goo.gl/E2EOrigin');
  // A sidebar search must not restrict the nearest-place search.
  await page.getByPlaceholder('Tìm kiếm địa điểm, khu vực...').fill('Không khớp yêu cầu nào');
  await panel.getByRole('button', { name: 'Tìm đường', exact: true }).click();
  await expect(panel.getByRole('button', { name: 'Tìm đường', exact: true })).toBeEnabled();
  await expect(panel.getByText('Đã tìm thấy 5 địa điểm gần bạn')).toBeVisible();
  await expect(panel.getByRole('listitem')).toHaveCount(5);
  await expect(panel.getByRole('link', { name: 'Chỉ đường Google Maps' })).toHaveCount(5);
  expect(resolvedLinks).toEqual(['https://maps.app.goo.gl/E2EOrigin']);
  expect(routeRequests).toHaveLength(5);
  routeRequests.forEach((data, index) => {
    expect(data.start.coordinates).toEqual(origin);
    expect(data.end.coordinates).toEqual([origin[0], origin[1] + (index + 1) * 0.01]);
  });
  await expect(panel.getByText('Đường đi: 1,5 km · 5 phút')).toHaveCount(4);
  await expect(panel.getByText('Kết nối thử bị gián đoạn.')).toBeVisible();
  const destinations = await panel.getByRole('link', { name: 'Chỉ đường Google Maps' }).evaluateAll((links) =>
    links.map((link) => new URL(link.href).searchParams.get('destination')));
  expect(new Set(destinations).size).toBe(5);
  await expect(page.locator('[title^="Điểm "]')).toHaveCount(5);
  await page.screenshot({ path: 'test-results/nearby-routes.png', fullPage: true });
  await page.getByRole('button', { name: 'Thu gọn bảng điều khiển', exact: true }).click();
  await expect(panel).toHaveCount(0);
  await page.getByRole('button', { name: 'Mở bảng điều khiển', exact: true }).click();
  await expect(panel.getByRole('listitem')).toHaveCount(5);
  await expect(panel.getByLabel('Link Google Maps vị trí hiện tại')).toHaveValue('https://maps.app.goo.gl/E2EOrigin');
  await panel.getByRole('button', { name: 'Xóa đường', exact: true }).click();
  await expect(panel.getByRole('listitem')).toHaveCount(0);
  await expect(page.locator('[title^="Điểm "]')).toHaveCount(0);
});

test('an unresolved shared link reports an error without keeping previous directions', async ({ page }) => {
  await page.route('https://tile.openstreetmap.org/**', (route) => route.abort());
  await page.route('**/api/auth/me', (route) => route.fulfill({ json: {
    user: { id: 1, name: 'Vận hành thử', role: 'operator' }, csrf_token: 'test-csrf',
  } }));
  await page.route('**/api/jobs', (route) => route.fulfill({ json: [] }));
  await page.route('**/api/geocode/status', (route) => route.fulfill({ json: { configured: false } }));
  await page.route('**/api/geocode/resolve-link', (route) => route.fulfill({ status: 404,
    json: { detail: 'Link này chưa có ghim vị trí.' } }));
  await page.goto('/');
  const panel = page.getByRole('region', { name: 'Tìm đường tới các địa điểm thiên tai' });
  await expect(page.getByText('Vận hành thử · Vận hành')).toBeVisible();
  await expect(page.getByRole('heading', { name: /^Điểm demo E2E/ })).toBeVisible();
  await panel.getByLabel('Link Google Maps vị trí hiện tại').fill('https://maps.google.com/?q=16.46,107.58');
  await panel.getByRole('button', { name: 'Tìm đường', exact: true }).click();
  await expect(panel.getByRole('listitem')).toHaveCount(1);
  await panel.getByLabel('Link Google Maps vị trí hiện tại').fill('https://maps.app.goo.gl/NoPin');
  await panel.getByRole('button', { name: 'Tìm đường', exact: true }).click();
  await expect(panel.getByText('Link này chưa có ghim vị trí.')).toBeVisible();
  await expect(panel.getByRole('listitem')).toHaveCount(0);
});
