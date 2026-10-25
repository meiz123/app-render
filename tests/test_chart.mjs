import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildTimeline, axisMaximum } from '../framelab/static/js/chart-model.js';

test('time buckets retain gaps, maxima, deadlines and frozen counts',()=>{
  const frames=[
    {IntendedVsync:1e9,duration_ms:10,FrameDeadline:1e9+16e6,FrameCompleted:1e9+10e6},
    {IntendedVsync:1.01e9,duration_ms:800,FrameDeadline:1.01e9+16e6,FrameCompleted:1.01e9+800e6},
    {IntendedVsync:10e9,duration_ms:20},
    {IntendedVsync:2e9,duration_ms:NaN},
  ];
  const model=buildTimeline(frames,1e9,3);
  assert.equal(model.seconds,9);assert.equal(model.count,3);assert.equal(model.peak,800);
  assert.equal(model.buckets[0].peak,800);assert.equal(model.buckets[0].missed,1);
  assert.equal(model.buckets[0].frozen,1);assert.equal(model.buckets[1].peak,null);
});
test('detail cap never changes real data and full scale contains outlier',()=>{
  assert.equal(axisMaximum(1600,'detail'),50);
  assert.ok(axisMaximum(1600,'all')>1600);
  assert.equal(buildTimeline([]),null);
});
