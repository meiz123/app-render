import assert from 'node:assert/strict';
import { test } from 'node:test';

class Element {
  constructor() { this.value = ''; this.disabled = false; this.hidden = false; this.textContent = ''; this.parentElement = {hidden:false}; }
  setAttribute(name, value) { this[name] = value; }
  append(...children) { this.children = [...(this.children || []), ...children]; }
  replaceChildren(...children) { this.children = children; this.value = children[0]?.value || ''; }
}
const elements = new Map();
globalThis.document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
  createElement() { return new Element(); },
};
const { state, $ } = await import('../framelab/static/js/common.js');
const { loadPackages, filterPackages } = await import('../framelab/static/js/devices.js');

test('connected device loads apps through the real package route and enables selection', async () => {
  state.phase = 'idle'; state.installing = false; state.appMode = 'package';
  $('device').value = 'test-device';
  globalThis.fetch = async (path) => {
    if (path.startsWith('/api/apps?')) return {ok:true,json:async()=>({apps:[{package:'com.example.gallery', label:'Thư viện ảnh', label_available:true, icon:null}],warning:null})};
    assert.equal(path, '/api/packages?serial=test-device');
    return {ok:true,json:async()=>({packages:['com.android.settings','com.example.gallery','com.example.gallery.debug']})};
  };
  await loadPackages();
  assert.equal($('package').disabled, false);
  assert.equal($('start').disabled, false);
  $('package-search').value = '  COM.EXAMPLE.GALLERY  ';
  filterPackages();
  assert.equal($('package').value, 'com.example.gallery');
  assert.equal($('package').children.length, 2);
  $('package-search').value = 'not.installed'; filterPackages();
  assert.equal($('start').disabled, true);
  assert.match($('package-status').textContent, /Không khớp package/);
  $('package-search').value = ''; filterPackages();
  assert.equal($('package').children.length, 3);
  assert.equal($('start').disabled, false);
});

import { matchingPackages } from '../framelab/static/js/app-picker.js';
test('name mode searches real labels without accents and package mode searches IDs', () => {
  state.appMode = 'name';
  assert.deepEqual(matchingPackages('thu vien'), ['com.example.gallery']);
  state.appMode = 'package';
  assert.deepEqual(matchingPackages('com.android'), ['com.android.settings']);
});
