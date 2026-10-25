import { $, state, controls } from './common.js';

export function searchableName(value) {
  return value.normalize('NFD').replace(/\p{Diacritic}/gu, '').replace(/đ/gi, 'd').toLowerCase();
}

export function matchingPackages(query) {
  const byPackage = new Map(state.apps.map(app => [app.package, app]));
  const needle = searchableName(query.trim());
  return state.packages.filter(packageId => {
    const name = state.appMode === 'name' ? byPackage.get(packageId)?.label || packageId : packageId;
    return searchableName(name).includes(needle);
  });
}

function icon(app) {
  if (app?.icon?.startsWith('data:image/png;base64,')) {
    const image = document.createElement('img');
    image.src = app.icon;
    image.alt = '';
    image.width = image.height = 30;
    image.loading = 'lazy';
    return image;
  }
  const fallback = document.createElement('span');
  fallback.className = 'app-icon-fallback';
  fallback.textContent = '▧';
  fallback.setAttribute('aria-label', 'Không có icon');
  return fallback;
}

export function renderPicker(matches, placeholder, onChange) {
  const byPackage = new Map(state.apps.map(app => [app.package, app]));
  const selected = byPackage.get($('package').value);
  const nameMode = state.appMode === 'name';
  $('package').hidden = nameMode;
  $('app-picker-trigger').parentElement.hidden = !nameMode;
  $('mode-name').setAttribute('aria-pressed', String(nameMode));
  $('mode-package').setAttribute('aria-pressed', String(!nameMode));
  $('package-search').placeholder = nameMode ? 'Tìm theo tên app…' : 'Tìm theo package ID…';
  const title = document.createElement('span');
  title.className = 'app-selected-label';
  title.textContent = $('package').value ? selected?.label || $('package').value : placeholder;
  $('app-picker-trigger').replaceChildren(icon(selected), title);
  $('app-picker-list').replaceChildren(...matches.map(packageId => {
    const app = byPackage.get(packageId);
    const row = document.createElement('button');
    row.type = 'button';
    row.className = 'app-option';
    row.setAttribute('role', 'option');
    row.setAttribute('aria-selected', String(packageId === $('package').value));
    const labels = document.createElement('span');
    const name = document.createElement('strong');
    name.textContent = app?.label || packageId;
    const detail = document.createElement('small');
    detail.textContent = app?.label_available ? packageId : 'Chưa lấy được tên app · ' + packageId;
    labels.append(name, detail);
    row.append(icon(app), labels);
    row.onclick = () => {
      $('package').value = packageId;
      closePicker();
      onChange(packageId);
      controls();
    };
    row.onkeydown = event => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        const next = event.key === 'ArrowDown' ? row.nextElementSibling : row.previousElementSibling;
        next?.focus();
      }
    };
    return row;
  }));
}

function closePicker() {
  $('app-picker-list').hidden = true;
  $('app-picker-trigger').setAttribute('aria-expanded', 'false');
}

export function initAppPicker(onChange) {
  for (const [id, mode] of [['mode-name', 'name'], ['mode-package', 'package']]) {
    $(id).onclick = () => {
      state.appMode = mode;
      $('package-search').value = '';
      closePicker();
      onChange();
    };
  }
  $('app-picker-trigger').onclick = () => {
    const show = $('app-picker-list').hidden;
    $('app-picker-list').hidden = !show;
    $('app-picker-trigger').setAttribute('aria-expanded', String(show));
    if (show) $('app-picker-list').querySelector('[aria-selected="true"]')?.focus();
  };
  document.addEventListener('click', event => {
    if (!event.target.closest('.app-picker')) closePicker();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !$('app-picker-list').hidden) {
      closePicker();
      $('app-picker-trigger').focus();
    }
  });
}
