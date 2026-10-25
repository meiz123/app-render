/** Time-based groups retain peaks; empty time intervals remain empty. */
export function buildTimeline(frames, originNs, limit = 90) {
  const valid = frames.filter(frame => Number.isFinite(frame.duration_ms) && frame.duration_ms > 0 && Number.isFinite(frame.IntendedVsync));
  if (!valid.length) return null;
  const sorted = [...valid].sort((a, b) => a.IntendedVsync - b.IntendedVsync);
  const origin = Number.isFinite(originNs) ? originNs : sorted[0].IntendedVsync;
  const end = Math.max(0.001, (sorted.at(-1).IntendedVsync - origin) / 1e9);
  const count = Math.min(limit, sorted.length);
  const buckets = Array.from({ length: count }, (_, index) => ({
    start: index * end / count, end: (index + 1) * end / count, frames: [],
  }));
  for (const frame of sorted) {
    const elapsed = Math.max(0, (frame.IntendedVsync - origin) / 1e9);
    buckets[Math.min(count - 1, Math.floor(elapsed / end * count))].frames.push(frame);
  }
  for (const bucket of buckets) {
    bucket.peak = bucket.frames.length ? Math.max(...bucket.frames.map(frame => frame.duration_ms)) : null;
    bucket.missed = bucket.frames.filter(frame => Number.isFinite(frame.FrameDeadline) && frame.FrameDeadline > frame.IntendedVsync && frame.FrameCompleted > frame.FrameDeadline).length;
    bucket.frozen = bucket.frames.filter(frame => frame.duration_ms > 700).length;
  }
  return { buckets, seconds: end, count: sorted.length, peak: Math.max(...sorted.map(frame => frame.duration_ms)) };
}

export function axisMaximum(peak, mode) {
  if (mode === 'detail') return 50;
  const raw = Math.max(50, peak * 1.1);
  const step = 10 ** Math.floor(Math.log10(raw));
  return Math.ceil(raw / step) * step;
}
