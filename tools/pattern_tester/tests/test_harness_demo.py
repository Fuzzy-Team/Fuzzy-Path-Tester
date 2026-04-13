from tools.pattern_tester.backend.runner import Runner
from tools.pattern_tester.backend.visualizer import trace_segments


def test_smoke():
    assert True


def test_skillet_trace_uses_macro_walk_units():
    result = Runner().run_blocking(
        'patterns/skillet.py',
        sizeword='M',
        width=4,
        movespeed=18,
        time_scale=0.0,
    )

    assert result.success
    segments, bounds = trace_segments(result.selfstub.keyboard_events, shift_lock=True)

    assert len(segments) == 42
    assert segments[0]['keys'] == 'd'
    assert abs(segments[0]['distance'] - 0.916) < 1e-9
    assert bounds['total_distance'] > 19.0
    assert any(segment['yaw_degrees'] for segment in segments)


def test_camera_yaw_only_changes_movement_with_shift_lock():
    result = Runner().run_blocking(
        'patterns/skillet.py',
        sizeword='M',
        width=4,
        movespeed=18,
        time_scale=0.0,
    )

    assert result.success
    unlocked_segments, unlocked_bounds = trace_segments(result.selfstub.keyboard_events)
    locked_segments, locked_bounds = trace_segments(result.selfstub.keyboard_events, shift_lock=True)

    assert any(segment['camera_yaw_degrees'] for segment in unlocked_segments)
    assert not any(segment['yaw_degrees'] for segment in unlocked_segments)
    assert any(segment['yaw_degrees'] for segment in locked_segments)
    assert unlocked_bounds['end_x'] != locked_bounds['end_x']
    assert unlocked_bounds['end_y'] != locked_bounds['end_y']
