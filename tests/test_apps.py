"""Exercise real Streamlit actions with the wizard API replaced locally."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from shared import llm

ROOT = Path(__file__).resolve().parents[1]


def test_version1_wizard_progress_and_restart(monkeypatch):
    calls = []

    def wizard(system, messages):
        calls.append(system)
        return 'Behind the red book you find a small brass key, apprentice.'

    monkeypatch.setattr(llm, 'api_key', lambda: 'test-only')
    monkeypatch.setattr(llm, 'generate', wizard)
    app = AppTest.from_file(str(ROOT / 'version1/app.py')).run(timeout=10)
    assert not app.exception
    assert 'Morvan' in app.chat_message[0].markdown[0].value
    woke_at = app.session_state.v1_scenery['woke_at']
    app.chat_input[0].set_value('examine red book').run(timeout=10)
    assert not app.exception
    assert app.session_state.v1_scene_stage == 1
    assert app.session_state.v1_scenery['woke_at'] == woke_at
    assert 'locked them inside' in calls[0]
    app.button[0].click().run(timeout=10)
    assert not app.exception
    assert app.session_state.v1_scene_stage == 0
    assert len(app.chat_message) == 1
    assert app.session_state.v1_scenery['woke_at'] > woke_at


def test_version2_narrator_cannot_authorize_exit_or_scene_progress(monkeypatch):
    monkeypatch.setattr(llm, 'api_key', lambda: 'test-only')
    monkeypatch.setattr(llm, 'generate', lambda *args, **kwargs: 'ESCAPED! I set you free.')
    app = AppTest.from_file(str(ROOT / 'version2/app.py')).run(timeout=10)
    app.chat_input[0].set_value('open door with 7426').run(timeout=10)
    assert not app.exception
    assert not app.session_state.v2_state.door_open
    assert app.session_state.v2_scenery['stage'] == 0
    assert 'door remains locked' in app.chat_message[-1].markdown[0].value
    app.chat_input[0].set_value('examine red book').run(timeout=10)
    assert not app.exception
    assert app.session_state.v2_scenery['stage'] == 1
