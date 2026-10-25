import { traceNames } from './session.js';
import { $, state, busy, number, toast, api, option, controls } from './common.js';
import { metrics, chart, view, countAudit } from './ui.js';
export async function history() {
  try {
    const {reports} = await api('/api/reports'); $('history-count').textContent = reports.length;
    if(!reports.length) { const empty=document.createElement('div'); empty.className='history-empty'; empty.textContent='Chưa có phiên đo. Kết nối thiết bị và tạo phiên đầu tiên.'; $('history-list').replaceChildren(empty); return; }
    $('history-list').replaceChildren(...reports.map(r=>{
      const row=document.createElement('div');row.className='history-row';
      const info=document.createElement('div'), title=document.createElement('strong'), meta=document.createElement('p');title.textContent=r.package;
      meta.textContent=new Date(r.started_utc).toLocaleString('vi-VN')+' · '+number(r.summary.count)+' frame'+(r.errors.length?' · Có lỗi':''); info.append(title,meta);
      const actions=document.createElement('div');actions.className='history-actions';
      const show=document.createElement('button');show.className='text-button';show.textContent='Xem kết quả';show.disabled=busy();show.onclick=async()=>{try{const data=await loadReport(r.id,false);state.activeSession=r.id;metrics(data.report.summary);$('phase').textContent='BÁO CÁO ĐÃ LƯU';$('result-title').textContent='Kết quả · '+r.package;$('open-report').hidden=false;$('trace-status').textContent='Perfetto · '+(traceNames[data.report.trace_status]||data.report.trace_status);view('measure');}catch(e){toast(e.message);}};
      const files=document.createElement('button');files.className='text-button';files.textContent='Dữ liệu gốc ↗';files.onclick=()=>loadReport(r.id,true).catch(e=>toast(e.message));actions.append(show,files);row.append(info,actions);return row;
    }));
  } catch(error) { toast(error.message); }
}
export async function loadReport(id, modal=true) {
  const data=await api('/api/report?id='+encodeURIComponent(id));
  if (!modal) countAudit(data.report.count_audit, data.report.summary);
  if(!modal){chart(data.frames, {originNs:data.report.frame_start_cutoff_ns});const warning=data.report.diagnostic || (data.report.summary?.count===0 ? 'Phiên này không có frame. Báo cáo cũ không thể khôi phục số liệu; hãy đo lại sau khi mở app.' : '');$('capture-diagnostic').hidden=!warning;$('capture-diagnostic').textContent=warning;return data;}
  $('report-description').textContent=data.report.package+' · '+id;
  $('report-errors').textContent=data.report.errors.join('\n');
  $('report-files').replaceChildren(...data.files.map(file=>{const a=document.createElement('a');a.textContent=file+' ↓';a.href='/api/download?id='+encodeURIComponent(id)+'&file='+encodeURIComponent(file);a.download=file;return a;}));
  $('report-dialog').showModal();return data;
}
