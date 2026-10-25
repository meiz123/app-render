import { $, number } from './common.js';
import { buildTimeline, axisMaximum } from './chart-model.js';
import { slowFrames } from './slow-frames.js';

let mode = 'detail';
let latestFrames = [];
let latestOptions = {};
let contextKey = null;
const NS = 'http://www.w3.org/2000/svg';

function svgNode(name, attrs = {}, content) {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  if (content !== undefined) node.textContent = content;
  return node;
}

export function chart(frames, options = {}) {
  latestFrames = frames;
  latestOptions = options;
  // Old Android reset responses can contain the previous session timestamp.
  // Anchor visualization to the first observed frame, never a stale reset.
  const timeline = buildTimeline(frames);
  const root = $('chart');
  root.classList.add('timeline-chart');
  root.replaceChildren();
  if (!timeline) {
    const empty = document.createElement('div');
    empty.className = 'timeline-empty';
    empty.textContent = 'Chưa có frame hợp lệ. Mở app mục tiêu và thao tác để bắt đầu ghi nhận.';
    root.append(empty);
    return;
  }
  const newContext = options.originNs ?? frames[0]?.IntendedVsync;
  if (contextKey !== newContext) { mode = 'detail'; contextKey = newContext; }
  const header = document.createElement('div');
  header.className = 'timeline-toolbar';
  const summary = document.createElement('span');
  summary.textContent = `${number(timeline.count)} frame hiển thị · Đỉnh ${number(timeline.peak, 1)} ms`;
  const select = document.createElement('select');
  select.setAttribute('aria-label', 'Thang hiển thị biểu đồ');
  for (const [value, label] of [['detail', 'Chi tiết · 0–50 ms'], ['all', 'Toàn bộ giá trị']]) {
    const option = document.createElement('option');
    option.value = value; option.textContent = label; select.append(option);
  }
  select.value = mode;
  select.onchange = () => { mode = select.value; chart(latestFrames, latestOptions); };
  header.append(summary, select);

  const legend = document.createElement('div');
  legend.className = 'timeline-legend';
  for (const [className, label] of [['normal', 'Thời gian frame'], ['late', 'Có frame trễ deadline'], ['frozen', '> 700 ms']]) {
    const item = document.createElement('span');
    const dot = document.createElement('i'); dot.className = className;
    item.append(dot, document.createTextNode(label)); legend.append(item);
  }

  const viewport = document.createElement('div');
  viewport.className = 'timeline-viewport';
  const svg = svgNode('svg', { viewBox: '0 0 760 268', role: 'img', 'aria-label': 'Thời gian frame theo giây, đơn vị mili giây', preserveAspectRatio: 'none' });
  const left = 48, right = 735, top = 28, bottom = 222;
  const width = right - left, height = bottom - top;
  const maximum = axisMaximum(timeline.peak, mode);
  const y = value => bottom - Math.min(value, maximum) / maximum * height;
  svg.append(svgNode('text', { x: 8, y: 14, class: 'axis-title' }, 'ms'));
  for (let i = 0; i <= 5; i++) {
    const value = i * maximum / 5;
    svg.append(svgNode('line', { x1: left, x2: right, y1: y(value), y2: y(value), class: 'grid-line' }));
    svg.append(svgNode('text', { x: left - 10, y: y(value) + 4, 'text-anchor': 'end', class: 'axis-label' }, number(value)));
  }
  const reference = 1000 / 60;
  svg.append(svgNode('line', { x1: left, x2: right, y1: y(reference), y2: y(reference), class: 'reference-line' }));
  svg.append(svgNode('text', { x: right, y: y(reference) - 7, 'text-anchor': 'end', class: 'reference-label' }, '16,7 ms · mốc 60 Hz'));
  for (let i = 0; i <= 4; i++) {
    const x = left + i * width / 4;
    svg.append(svgNode('text', { x, y: 244, 'text-anchor': i === 0 ? 'start' : i === 4 ? 'end' : 'middle', class: 'axis-label' }, number(timeline.seconds * i / 4, 1) + ' s'));
  }
  svg.append(svgNode('text', { x: (left + right) / 2, y: 265, 'text-anchor': 'middle', class: 'axis-title' }, 'Thời gian từ frame đầu tiên hiển thị'));
  const tooltip = document.createElement('div');
  tooltip.className = 'timeline-tooltip';
  tooltip.setAttribute('role', 'status');
  tooltip.textContent = 'Rê chuột, chạm hoặc dùng Tab để xem từng khoảng thời gian.';
  for (const [index, bucket] of timeline.buckets.entries()) {
    if (bucket.peak === null) continue;
    const x = left + (index + 0.1) * width / timeline.buckets.length;
    const bw = Math.max(2, width / timeline.buckets.length * 0.8);
    const clipped = bucket.peak > maximum;
    const classification = bucket.frozen ? 'frozen' : bucket.missed ? 'late' : 'normal';
    const group = svgNode('g', { tabindex: 0, role: 'button', class: 'timeline-point', 'aria-label': `${number(bucket.start, 2)} đến ${number(bucket.end, 2)} giây, cao nhất ${number(bucket.peak, 2)} mili giây` });
    group.append(svgNode('rect', { x, y: y(bucket.peak), width: bw, height: Math.max(2, bottom - y(bucket.peak)), rx: 2, class: 'timeline-bar ' + classification }));
    if (clipped) group.append(svgNode('path', { d: `M ${x - 1} ${top - 5} L ${x + bw / 2} ${top - 12} L ${x + bw + 1} ${top - 5} Z`, class: 'overflow-marker ' + classification }));
    group.append(svgNode('rect', { x: x - 1, y: top - 14, width: bw + 2, height: height + 14, fill: 'transparent' }));
    const describe = () => {
      tooltip.textContent = `${number(bucket.start, 2)}–${number(bucket.end, 2)} s · ${bucket.frames.length} frame · Cao nhất ${number(bucket.peak, 2)} ms · ${bucket.missed} trễ deadline · ${bucket.frozen} trên 700 ms` + (clipped ? ' · Đỉnh vượt thang 50 ms, chọn “Toàn bộ giá trị” để xem.' : '');
    };
    group.onmouseenter = describe; group.onfocus = describe; group.onclick = describe;
    group.onkeydown = event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); describe(); }
    };
    svg.append(group);
  }
  viewport.append(svg);
  const note = document.createElement('p');
  note.className = 'timeline-note';
  const clippedCount = timeline.buckets.filter(bucket => bucket.peak > maximum).length;
  note.textContent = (clippedCount ? `▲ ${clippedCount} khoảng vượt ${maximum} ms; giá trị thật vẫn được giữ. ` : '') +
    'Mỗi cột là giá trị cao nhất trong một khoảng thời gian. Mốc 16,7 ms chỉ tham chiếu 60 Hz; màu trễ dùng deadline thực khi có dữ liệu.';
  root.append(header, legend, viewport, tooltip, note);
  root.append(slowFrames(frames));
}
