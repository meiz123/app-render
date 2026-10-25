import { initAppPicker } from './app-picker.js';
import { $, state, busy, number, toast, api, option, controls } from './common.js';
import { scan, loadPackages, filterPackages } from './devices.js';
import { metrics, view } from './ui.js';
import { showStatus, poll } from './session.js';
import { history, loadReport } from './reports.js';
$('refresh-top').onclick=scan;
$('device').onchange=loadPackages;
$('reload-packages').onclick=()=>loadPackages(true);
$('package').onchange=controls;
initAppPicker(filterPackages);
$('package-search').oninput=filterPackages;
$('start').onclick=async()=>{
  state.starting=true;controls();toast('Đang mở app trên điện thoại…');
  try {const data=await api('/api/start',{serial:$('device').value,package:$('package').value,seconds:Number($('duration').value)});metrics(null);const note=document.createElement('div');note.className='empty-chart';note.textContent='Đang thu dữ liệu. Biểu đồ xuất hiện sau khi hoàn tất phiên.';$('chart').replaceChildren(note);showStatus(data);toast('Đang ghi. Hãy thao tác trong app đã chọn trên điện thoại.');}
  catch(error){toast(error.message);}
  finally{state.starting=false;controls();}
};
$('stop').onclick=async()=>{try{await api('/api/stop',{});$('stop').disabled=true;toast('Đã yêu cầu dừng lấy mẫu. Đợi trace hoàn tất theo thời lượng đã đặt.');}catch(error){toast(error.message);}};
$('upload-button').onclick=()=>$('apk').click();
$('apk').onchange=async()=>{
  const file=$('apk').files[0];if(!file)return;
  if(!file.name.toLowerCase().endsWith('.apk') || file.size>140*1024*1024){toast('Chọn APK không quá 140 MB.');$('apk').value='';return;}
  state.installing=true;controls();toast('Đang cài APK. Giữ kết nối USB…');
  try {const base64=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.onerror=reject;r.readAsDataURL(file);});await api('/api/install',{serial:$('device').value,apk:base64});await loadPackages();toast('Đã cài APK. Chọn đúng package trong danh sách ứng dụng.');}
  catch(error){toast(error.message);}
  finally{state.installing=false;controls();$('apk').value='';}
};
$('nav-measure').onclick=()=>view('measure');$('nav-history').onclick=()=>view('history');$('reload-history').onclick=history;
$('open-report').onclick=()=>loadReport(state.activeSession,true).catch(e=>toast(e.message));$('close-dialog').onclick=()=>$('report-dialog').close();
(async()=>{try{state.token=(await api('/api/bootstrap')).token;await Promise.all([scan(),history(),poll()]);setInterval(poll,1200);}catch(error){toast(error.message);}})();

$('quit').onclick = async () => {
  try {
    await api('/api/shutdown', {});
    state.closed = true;
    $('measure-view').inert = true;
    $('history-view').inert = true;
    $('phase').textContent = 'ĐÃ ĐÓNG';
    $('quit').disabled = true;
    toast('Frame Lab đã đóng. Bạn có thể đóng tab và mở lại app khi cần.');
  } catch (error) { toast(error.message); }
};
