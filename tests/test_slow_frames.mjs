import {test} from 'node:test';
import assert from 'node:assert/strict';
import {rankFrames} from '../framelab/static/js/slow-frames.js';
test('slow frames keep temporal identity when ranked by duration',()=>{
 const rows=rankFrames([{IntendedVsync:1e9,duration_ms:10},{IntendedVsync:2e9,duration_ms:50,FrameCompleted:2.05e9,FrameDeadline:2.02e9,FrameTimelineVsyncId:123}]);
 assert.equal(rows[0].index,2);assert.equal(rows[0].elapsed,1);assert.equal(rows[0].overrun,30);assert.equal(rows[0].frame.FrameTimelineVsyncId,123);assert.equal(rows[1].overrun,null);
});
