import { number } from './common.js';

export function rankFrames(frames) {
  const sorted = frames.filter(f => Number.isFinite(f.duration_ms) && f.duration_ms > 0)
    .sort((a, b) => a.IntendedVsync - b.IntendedVsync);
  const origin = sorted[0]?.IntendedVsync || 0;
  return sorted.map((frame, index) => {
    const hasDeadline = Number.isFinite(frame.FrameDeadline) && frame.FrameDeadline > frame.IntendedVsync && frame.FrameDeadline < 2**63 - 1;
    return { frame, index: index + 1, elapsed: (frame.IntendedVsync - origin) / 1e9,
      overrun: hasDeadline ? Math.max(0, (frame.FrameCompleted - frame.FrameDeadline) / 1e6) : null };
  }).sort((a, b) => b.frame.duration_ms - a.frame.duration_ms).slice(0, 20);
}

export function slowFrames(frames) {
  const section = document.createElement('section');
  section.className = 'slow-frames';
  const title = document.createElement('h3'); title.textContent = 'Các frame chậm nhất';
  const note = document.createElement('p'); note.className = 'timeline-note';
  note.textContent = 'Tối đa 20 frame theo thời lượng giảm dần. # là thứ tự trong mẫu đang hiển thị; ID là mã Android nếu có. Bấm dòng để xem chi tiết.';
  const viewport = document.createElement('div'); viewport.className = 'slow-table-scroll';
  const table = document.createElement('table');
  const thead = document.createElement('thead'), header = document.createElement('tr');
  for (const label of ['Frame / ID', 'Thời điểm', 'Thời lượng', 'Trễ deadline', 'Activity / cửa sổ']) {
    const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = label; header.append(cell);
  }
  thead.append(header); table.append(thead);
  const tbody = document.createElement('tbody');
  const detail = document.createElement('div'); detail.className = 'frame-detail'; detail.hidden = true;
  detail.setAttribute('role', 'status');
  for (const item of rankFrames(frames)) {
    const { frame, index, elapsed, overrun } = item;
    const id = frame.FrameTimelineVsyncId;
    const row = document.createElement('tr');
    const cell = document.createElement('td'), button = document.createElement('button');
    button.className = 'text-button'; button.textContent = `#${index}` + (id != null ? ` · ID ${id}` : '');
    cell.append(button); row.append(cell);
    const activity = frame.window?.split('/').slice(1).join('/') || frame.window || 'Chưa có dữ liệu';
    for (const value of [number(elapsed, 2) + ' s', number(frame.duration_ms, 2) + ' ms',
      overrun === null ? 'Không có deadline' : number(overrun, 2) + ' ms', activity]) {
      const td = document.createElement('td'); td.textContent = value; td.title = value; row.append(td);
    }
    if (overrun > 0) row.className = 'late-frame';
    const select = () => {
      for (const sibling of tbody.children) sibling.classList.remove('selected-frame');
      row.classList.add('selected-frame'); detail.hidden = false;
      detail.textContent = `Frame #${index}${id != null ? ' · Android ID ' + id : ''} · ${number(elapsed, 3)} s từ frame đầu · ${number(frame.duration_ms, 3)} ms · ` +
        (overrun === null ? 'Không có deadline trong nguồn dữ liệu.' : `Trễ ${number(overrun, 3)} ms so với deadline.`) +
        `\nCửa sổ: ${frame.window || 'Báo cáo này chưa ghi Activity/cửa sổ; phiên mới sẽ lưu nếu Android cung cấp.'}` +
        '\nĐây là định danh frame, chưa xác định tên thao tác hoặc nguyên nhân gây chậm.';
    };
    button.onclick = select; row.onclick = select;
    tbody.append(row);
  }
  table.append(tbody); viewport.append(table); section.append(title, note, viewport, detail);
  return section;
}
