import { $, state, busy, number, toast, api, option, controls } from './common.js';
import { metrics, chart, countAudit } from './ui.js';
import { loadReport, history } from './reports.js';
export const traceNames = {not_started:'Chưa ghi trace',recording:'Đang ghi',saved_unvalidated:'Đã lưu · chưa xác thực độ bao phủ',failed:'Ghi thất bại',requires_android_12:'FrameTimeline cần Android 12+'};
export function showStatus(data) {
  const old = state.phase;
  if (old === data.phase && ['idle','complete'].includes(old) && $('phase').textContent === 'BÁO CÁO ĐÃ LƯU') return;
  state.phase = data.phase;
  state.activeSession = data.session || state.activeSession;
  const labels = {idle:'CHƯA BẮT ĐẦU',recording:'ĐANG GHI',finalizing:'ĐANG LƯU TRACE',complete:'ĐÃ KẾT THÚC',error:'CÓ LỖI'};
  $('phase').textContent = labels[state.phase] || state.phase;
  $('result-title').textContent = state.phase === 'recording' ? 'Đang ghi · ' + number(data.elapsed_s || 0) + ' / ' + data.seconds + ' giây' : state.phase === 'finalizing' ? 'Đang hoàn tất trace…' : 'Tổng quan rendering';
  $('live-dot').classList.toggle('recording',state.phase === 'recording');
  $('trace-status').textContent = 'Perfetto · ' + (traceNames[data.report?.trace_status || data.trace] || 'Chưa ghi trace');
  if (data.summary) metrics(data.summary);
  countAudit(data.report?.count_audit || data.count_audit, data.summary);
  if (data.frames?.length && state.phase !== 'complete') chart(data.frames, {originNs:data.frame_start_cutoff_ns});
  const diagnostic=data.diagnostic || data.report?.diagnostic || (data.report?.summary?.count===0 ? 'Không thu được frame trong phiên. Kiểm tra app đang chạy và dữ liệu gốc.' : '');
  $('capture-diagnostic').hidden=!diagnostic;
  $('capture-diagnostic').textContent=diagnostic;
  $('open-report').hidden = state.phase !== 'complete' || !state.activeSession;
  controls();
  if (old !== state.phase && state.phase === 'complete') {
    toast(data.report?.errors.length ? 'Phiên đo có lỗi. Mở dữ liệu gốc để xem chi tiết.' : 'Đã lưu phiên đo và dữ liệu gốc trên máy tính.');
    loadReport(state.activeSession,false).catch(e=>toast(e.message)); history();
  }
  if (old !== state.phase && state.phase === 'error') toast(data.error);
}
export async function poll() {
  if (state.polling || state.closed) return;
  state.polling = true;
  try { showStatus(await api('/api/status')); }
  catch (error) { $('trace-status').textContent = 'Không kết nối được máy chủ cục bộ. Kiểm tra cửa sổ chạy app.'; }
  finally { state.polling = false; }
}
