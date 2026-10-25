import { $, state, busy, toast, api, option, controls } from './common.js';
import { matchingPackages, renderPicker } from './app-picker.js';

let requestVersion = 0;

export async function scan() {
  if (busy()) return;
  $('refresh-top').disabled = true;
  try {
    const { devices } = await api('/api/devices');
    const ready = devices.filter(device => device.state === 'device');
    const previous = $('device').value;
    const options = ready.map(device => {
      const model = device.detail.match(/model:([^ ]+)/)?.[1]?.replaceAll('_', ' ') || 'Android';
      return option(device.serial, `${model} · ${device.serial}`);
    });
    $('device').replaceChildren(...(options.length ? options : [option('', 'Chưa có thiết bị kết nối')]));
    if (ready.some(device => device.serial === previous)) $('device').value = previous;
    $('connection-title').textContent = ready.length ? 'Thiết bị đã sẵn sàng' : 'Chưa có thiết bị được cấp quyền';
    $('connection-desc').textContent = ready.length
      ? 'USB đã kết nối. Chọn app trong danh sách hoặc tìm bằng package ID bên dưới.'
      : devices.length
        ? devices.map(device => `${device.serial}: ${device.state}`).join(' · ') + '. Hãy chấp nhận kết nối USB trên điện thoại.'
        : 'Kết nối USB, bật Gỡ lỗi USB và chấp nhận máy tính trên điện thoại.';
    $('connection-tag').textContent = ready.length ? 'ĐÃ KẾT NỐI' : 'CHỜ KẾT NỐI';
    await loadPackages();
  } catch (error) {
    $('connection-title').textContent = 'Không thể kiểm tra thiết bị';
    $('connection-desc').textContent = error.message;
    $('connection-tag').textContent = 'CẦN KIỂM TRA';
    $('device').replaceChildren(option('', 'Không kết nối được ADB'));
    state.packages = [];
    state.packagesError = error.message;
    state.packagesLoading = false;
    requestVersion++;
    filterPackages();
  } finally {
    controls();
  }
}

export async function loadPackages(refresh = false) {
  if (['recording', 'finalizing'].includes(state.phase)) return;
  const serial = $('device').value;
  const version = ++requestVersion;
  const previous = $('package').value;
  state.packages = [];
  state.apps = [];
  state.catalogWarning = '';
  state.catalogLoading = false;
  state.packagesError = '';
  state.packagesLoading = Boolean(serial);
  filterPackages();
  if (!serial) return;
  try {
    const data = await api('/api/packages?serial=' + encodeURIComponent(serial));
    if (version !== requestVersion || serial !== $('device').value) return;
    state.packages = data.packages;
    state.packagesLoading = false;
    state.catalogLoading = true;
    filterPackages(previous);
    try {
      const catalog = await api('/api/apps?serial=' + encodeURIComponent(serial) + (refresh === true ? '&refresh=1' : ''));
      if (version !== requestVersion || serial !== $('device').value) return;
      state.apps = catalog.apps;
      state.catalogWarning = catalog.warning || '';
    } catch (error) {
      state.catalogWarning = 'Không lấy được tên/icon. Bạn vẫn có thể chọn bằng package ID.';
    }
  } catch (error) {
    if (version !== requestVersion) return;
    state.packagesError = error.message;
    toast('Không tải được danh sách app: ' + error.message);
  } finally {
    if (version === requestVersion) {
      state.packagesLoading = false;
      state.catalogLoading = false;
      filterPackages($('package').value || previous);
    }
  }
}

export function filterPackages(previous) {
  const selected = typeof previous === 'string' ? previous : $('package').value;
  const needle = $('package-search').value.trim().toLowerCase();
  const matches = matchingPackages(needle);
  let placeholder = 'Không tìm thấy ứng dụng phù hợp';
  let status = `${matches.length} / ${state.packages.length} app · Tìm bằng ${state.appMode === 'name' ? 'tên app' : 'package ID'}.`;
  if (state.catalogLoading) status += ' Đang tải tên và icon…';
  if (state.catalogWarning) status += ' ' + state.catalogWarning;
  if (!$('device').value) {
    placeholder = 'Kết nối thiết bị để chọn app';
    status = 'Chưa kết nối thiết bị.';
  } else if (state.packagesLoading) {
    placeholder = 'Đang tải danh sách ứng dụng…';
    status = 'Đang đọc app đã cài trên điện thoại…';
  } else if (state.packagesError) {
    placeholder = 'Không tải được danh sách app';
    status = state.packagesError + ' · Bấm Làm mới để thử lại.';
  } else if (!state.packages.length) {
    placeholder = 'Không có app được trả về';
    status = 'Không đọc được app đã cài. Kiểm tra đúng thiết bị/hồ sơ Android rồi làm mới.';
  } else if (!matches.length) {
    status = 'Không khớp ' + (state.appMode === 'name' ? 'tên app' : 'package') + '. Xóa bộ lọc hoặc làm mới nếu vừa cài APK.';
  }
  $('package').replaceChildren(...(matches.length ? matches.map(value => option(value, value)) : [option('', placeholder)]));
  if (matches.includes(selected)) $('package').value = selected;
  else {
    const exact = matches.find(value => value.toLowerCase() === needle);
    if (exact) $('package').value = exact;
  }
  $('package-status').textContent = status;
  renderPicker(matches, placeholder, filterPackages);
  controls();
}
