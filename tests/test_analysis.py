import unittest
from framelab.domain.frames import parse_frames, summarize, frame_identity, android_rendered_total


class FrameAnalysisTests(unittest.TestCase):
    def test_revised_completion_does_not_create_new_frame(self):
        base = {"process_id": 123, "window": "app/Main", "IntendedVsync": 100,
                "FrameTimelineVsyncId": 50, "FrameCompleted": 200}
        revised = {**base, "FrameCompleted": 250}
        self.assertEqual(frame_identity(base), frame_identity(revised))
        self.assertNotEqual(frame_identity(base), frame_identity({**base, "window": "app/Dialog"}))
        self.assertNotEqual(frame_identity(base), frame_identity({**base, "process_id": 124}))
        no_id = {k: v for k, v in base.items() if k != "FrameTimelineVsyncId"}
        self.assertEqual(frame_identity(no_id), frame_identity({**no_id, "FrameCompleted": 250}))

    def test_platform_counter_does_not_add_window_subtotals(self):
        raw = '''** Graphics info for pid 1 [app] **
Total frames rendered: 100
Window: app/Main
Total frames rendered: 70
Window: app/Dialog
Total frames rendered: 30
** Graphics info for pid 2 [app:remote] **
Total frames rendered: 20
Window: app/Other
Total frames rendered: 20
'''
        self.assertEqual(android_rendered_total(raw), 120)

    def test_activity_context_is_preserved(self):
        raw = '''Window: com.example.app/.MainActivity
Flags,IntendedVsync,FrameCompleted,
0,1000000,9000000,
Window: com.example.app/.DetailsActivity
Flags,IntendedVsync,FrameCompleted,
0,2000000,12000000,
'''
        frames = parse_frames(raw)
        self.assertEqual(frames[0]["window"], "com.example.app/.MainActivity")
        self.assertEqual(frames[1]["window"], "com.example.app/.DetailsActivity")

    def test_android_framestats_trailing_commas(self):
        raw = '''---PROFILEDATA---
Flags,FrameTimelineVsyncId,IntendedVsync,Vsync,FrameDeadline,FrameCompleted,
0,123,1000000,1000000,17666666,19000000,
---PROFILEDATA---
'''
        frames = parse_frames(raw)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["duration_ms"], 18)
        self.assertEqual(summarize(frames)["deadline_miss_pct"], 100)

    def test_filters_flags_and_incomplete_frames(self):
        raw = '''Flags,IntendedVsync,FrameCompleted,FrameDeadline
0,1000000,11000000,17000000
1,2000000,12000000,18000000
0,3000000,9223372036854775807,19000000
0,4000000,4000000,20000000
'''
        frames = parse_frames(raw)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["duration_ms"], 10)

    def test_deadline_uses_device_deadline_not_fixed_60hz(self):
        frames = parse_frames('''Flags,IntendedVsync,FrameCompleted,FrameDeadline
0,1000000,13000000,9333333
0,20000000,721000000,36666667
''')
        result = summarize(frames)
        self.assertEqual(result["deadline_miss_pct"], 100)
        self.assertEqual(result["over_16_67_pct"], 50)
        self.assertEqual(result["frozen_pct"], 50)

    def test_unknown_is_not_zero_and_boundary_is_strict(self):
        self.assertIsNone(summarize([])["frozen_pct"])
        frame = {"IntendedVsync": 1, "FrameCompleted": 700000001, "duration_ms": 700}
        self.assertIsNone(summarize([frame])["deadline_miss_pct"])
        self.assertEqual(summarize([frame])["frozen_count"], 0)


if __name__ == "__main__":
    unittest.main()
