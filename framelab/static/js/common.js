export const $ = id => document.getElementById(id);
export const state = {token:'', packages:[], activeSession:null, phase:'idle', toastTimer:null, installing:false, polling:false, packagesLoading:false, packagesError:'', apps:[], appMode:'name', catalogLoading:false, catalogWarning:''};
export const busy = () => ['recording', 'finalizing'].includes(state.phase) || state.installing || state.starting;
export const number = (v, digits = 0) => v == null ? '—' : Number(v).toLocaleString('vi-VN', {maximumFractionDigits: digits, minimumFractionDigits: digits});
export function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => $('toast').hidden = true, 8000); }
export async function api(path, body) {
  const response = await fetch(path, body === undefined ? {cache:'no-store'} : {method:'POST', headers:{'Content-Type':'application/json','X-FrameLab-Token':state.token}, body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Không thể hoàn tất yêu cầu.');
  return data;
}
export function option(value, label) { const el = document.createElement('option'); el.value = value; el.textContent = label; return el; }
export function controls() {
  $('start').disabled = busy() || state.packagesLoading || !$('device').value || !$('package').value;
  for (const id of ['device','package','package-search','duration','refresh-top','upload-button']) $(id).disabled = busy();
  $('package').disabled = busy() || state.packagesLoading || !$('device').value || !state.packages.length;
  $('package-search').disabled = busy() || !$('device').value;
  $('reload-packages').disabled = busy() || state.packagesLoading || !$('device').value;
  $('app-picker-trigger').disabled = $('package').disabled;
  $('mode-name').disabled = busy();
  $('mode-package').disabled = busy();
  $('upload-button').disabled = busy() || !$('device').value;
  $('start').hidden = ['recording','finalizing'].includes(state.phase);
  $('stop').hidden = !['recording','finalizing'].includes(state.phase);
  $('stop').disabled = state.phase === 'finalizing';
  $('stop-note').hidden = $('stop').hidden;
}
