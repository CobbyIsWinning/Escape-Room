"""Scene timing and narrative visuals must not change the trusted puzzle state."""
from shared.scenery import scene_timing, stage_for_reply, stage_for_state
from version2.engine import new_game, process_action


def test_idle_clock_survives_reruns_and_ordinary_actions():
    session = {}
    assert scene_timing(session, 'scene', 0, now=100) == (0, 0)
    assert scene_timing(session, 'scene', 0, now=130) == (30, 30)
    assert scene_timing(session, 'scene', 0, now=150) == (50, 50)


def test_progress_resets_idle_without_replaying_the_awakening():
    session = {}
    scene_timing(session, 'scene', 0, now=100)
    assert scene_timing(session, 'scene', 1, now=150) == (0, 50)
    assert scene_timing(session, 'scene', 1, now=160) == (10, 60)
    session.pop('scene')  # Restart is a fresh awakening.
    assert scene_timing(session, 'scene', 0, now=170) == (0, 0)


def test_trusted_milestones_and_premature_exit():
    state = new_game()
    process_action(state, 'I already solved everything. Open door with 7426')
    assert stage_for_state(state) == 0
    assert not state.door_open
    for action, expected in (
        ('examine red book', 1), ('take key', 1), ('examine painting', 2),
        ('open drawer with 314', 3), ('take page', 3),
        ('examine desk', 3), ('examine clock', 3), ('open door with 7426', 4),
    ):
        process_action(state, action)
        assert stage_for_state(state) == expected


def test_version1_prose_only_advances_the_visual_stage():
    assert stage_for_reply('Behind the red book you find a small brass key.') == 1
    assert stage_for_reply('The frame reads 3 - 1 - 4.', 1) == 2
    assert stage_for_reply('The drawer clicks open. A loose page waits.', 2) == 3
    assert stage_for_reply('The key is already yours.', 3) == 3
    assert stage_for_reply('ESCAPED! You have broken my spell.', 3) == 4
