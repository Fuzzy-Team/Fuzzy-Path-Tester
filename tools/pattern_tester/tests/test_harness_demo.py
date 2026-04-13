from tools.pattern_tester.backend.runner import Runner
from tools.pattern_tester.backend.visualizer import trace_segments
from tools.pattern_tester.backend.fields import start_positions_for_field


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


def test_initial_turn_setting_does_not_flip_shift_lock_trace():
    base = Runner().run_blocking(
        'patterns/skillet.py',
        sizeword='M',
        width=1,
        movespeed=18,
        time_scale=0.0,
    )
    turned = Runner().run_blocking(
        'patterns/skillet.py',
        sizeword='M',
        width=1,
        movespeed=18,
        time_scale=0.0,
        turn='left',
        turn_times=4,
    )

    assert base.success
    assert turned.success
    _, base_bounds = trace_segments(base.selfstub.keyboard_events, shift_lock=True)
    _, turned_bounds = trace_segments(turned.selfstub.keyboard_events, shift_lock=True)

    assert abs(base_bounds['end_x'] - turned_bounds['end_x']) < 1e-9
    assert abs(base_bounds['end_y'] - turned_bounds['end_y']) < 1e-9


def test_pine_tree_field_context_clamps_to_field_map():
    result = Runner().run_blocking(
        'patterns/skillet.py',
        sizeword='M',
        width=1,
        movespeed=18,
        time_scale=0.0,
        turn='left',
        turn_times=4,
    )

    assert result.success
    segments, bounds = trace_segments(
        result.selfstub.keyboard_events,
        shift_lock=True,
        field_name='Pine Tree',
        start_position='upper left',
    )

    assert bounds['field_name'] == 'Pine Tree'
    assert bounds['start_x'] == 79.0
    assert bounds['start_y'] == 190.0
    assert any(segment['clamped'] for segment in segments)
    assert 0.0 <= bounds['end_x'] <= bounds['field_width']
    assert 0.0 <= bounds['end_y'] <= bounds['field_height']


def test_pine_tree_start_positions_are_available():
    starts = start_positions_for_field('Pine Tree')

    assert 'upper left' in starts
    assert 'center' in starts
    assert 'lower left' in starts
