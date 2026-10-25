export { chart } from './frame-chart.js';
import { $, state, busy, number, toast, api, option, controls } from './common.js';
import { history } from './reports.js';
export function metrics(summary) {
  $('metric-count').textContent = number(summary?.count);
  $('metric-deadline').textContent = summary?.deadline_miss_pct == null ? '—' : number(summary.deadline_miss_pct,2) + '%';
  $('metric-frozen').textContent = summary?.frozen_pct == null ? '—' : number(summary.frozen_pct,2) + '%';
  for (const p of [50,90,99]) $('p'+p).textContent = summary?.['p'+p+'_ms'] == null ? '—' : number(summary['p'+p+'_ms'],1) + ' ms';
}

export function countAudit(audit, summary) {
  const target = $('count-audit');
  target.hidden = !summary;
  if (!summary) return;
  if (!audit || audit.version !== 2) {
    target.textContent = 'Báo cáo dùng quy tắc đếm cũ; hãy đo lại để gộp các frame được Android cập nhật. Số này không phải FPS.';
    return;
  }
  target.textContent = `Đối chiếu: ${number(summary.count)} bản ghi frame cửa sổ duy nhất · Android báo ${number(audit.android_rendered_total)} frame ở lần đọc cuối · Đã gộp ${number(audit.revised_records_merged)} lần cập nhật thời điểm hoàn thành. ` +
    'Hai số có thể khác vì mẫu lọc frame không hợp lệ và bộ đệm có thể bỏ sót dữ liệu; không dùng số này làm FPS.';
}
export function view(name) {
  $('measure-view').hidden = name !== 'measure'; $('history-view').hidden = name !== 'history';
  $('nav-measure').classList.toggle('active',name === 'measure'); $('nav-history').classList.toggle('active',name === 'history');
  $('crumb').textContent = name === 'measure' ? 'Phiên đo' : 'Lịch sử báo cáo';
  if(name === 'history') history();
}
