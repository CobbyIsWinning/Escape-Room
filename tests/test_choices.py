"""Player choices must submit once, follow clues, and retain Python's authority."""
import json
from pathlib import Path
import re

from streamlit.testing.v1 import AppTest

from shared import llm
from shared.choices import OPENING_OPTIONS, choices_for_state, parse_turn
from shared.config import DRAWER_CODE, EXIT_CODE
from version2.engine import new_game

ROOT = Path(__file__).resolve().parents[1]


def buttons(app, prefix):
    return [button for button in app.button if button.key and button.key.startswith(prefix + '_reply_')]


def choose(app, text, prefix='v2'):
    choices = buttons(app, prefix)
    assert len(choices) == 3
    next(button for button in choices if button.label.split(' · ', 1)[1] == text).click().run(timeout=10)
    assert not app.exception


def test_initial_options_do_not_leak_codes_or_change_state():
    state = new_game()
    before = state.public_view()
    options = choices_for_state(state)
    assert len(options) == 3
    assert not re.search(r'\b\d{3,4}\b', ' '.join(options))
    assert state.public_view() == before and not state.history


def test_choice_parsing_recovers_without_showing_raw_json():
    reply, options = parse_turn(json.dumps({'dialogue': 'Which book calls to you?',
                                          'options': ['Read red book', 'Read red book', 42, 'Read blue book']}))
    assert reply == 'Which book calls to you?'
    assert len(options) == len(set(options)) == 3
    assert options[:2] == ('Read red book', 'Read blue book')
    reply, options = parse_turn('{"dialogue": "truncated')
    assert not reply.startswith('{') and len(options) == 3
    reply, options = parse_turn('You find a key behind the book.')
    assert reply.startswith('You find') and len(options) == 3


def test_version1_model_choices_are_displayed_and_submit_exact_reply(monkeypatch):
    received = []

    def wizard(system, messages, **kwargs):
        received.append(messages[-1]['content'])
        return json.dumps({'dialogue': 'Three bindings gleam. Which book will you examine?',
                           'options': ['Examine the red book', 'Inspect the blue book', 'Read the green book']})

    monkeypatch.setattr(llm, 'api_key', lambda: 'test-only')
    monkeypatch.setattr(llm, 'generate', wizard)
    app = AppTest.from_file(str(ROOT / 'version1/app.py')).run(timeout=10)
    choose(app, 'Examine the bookshelf', 'v1')
    assert [button.label.split(' · ', 1)[1] for button in buttons(app, 'v1')] == [
        'Examine the red book', 'Inspect the blue book', 'Read the green book']
    choose(app, 'Read the green book', 'v1')
    assert received == ['Examine the bookshelf', 'Read the green book']
    assert app.session_state.v1_messages[-2]['content'] == 'Read the green book'
    app.run(timeout=10)
    assert len(received) == 2
    app.button[0].click().run(timeout=10)
    assert tuple(button.label.split(' · ', 1)[1] for button in buttons(app, 'v1')) == OPENING_OPTIONS


def test_version2_can_be_completed_using_only_choices_and_rejects_wrong_answers(monkeypatch):
    monkeypatch.setattr(llm, 'api_key', lambda: '')
    app = AppTest.from_file(str(ROOT / 'version2/app.py')).run(timeout=10)
    choose(app, 'Examine the bookshelf')
    history = list(app.session_state.v2_state.history)
    app.run(timeout=10)
    assert app.session_state.v2_state.history == history
    choose(app, 'Examine the red book')
    choose(app, 'Take the key')
    choose(app, 'Inspect the painting')
    assert all(EXIT_CODE not in button.label for button in buttons(app, 'v2'))
    wrong = next(button for button in buttons(app, 'v2') if DRAWER_CODE not in button.label)
    wrong.click().run(timeout=10)
    assert not app.session_state.v2_state.unlocked_drawer
    assert 'incorrect' in app.session_state.v2_chat[-1]['content']
    choose(app, f'Open drawer with {DRAWER_CODE}')
    choose(app, 'Take the page')
    choose(app, 'Examine the desk')
    choose(app, 'Examine the clock')
    assert len(buttons(app, 'v2')) == 3
    choose(app, f'Open door with {EXIT_CODE}')
    assert app.session_state.v2_state.door_open
    assert app.session_state.v2_state.inventory == {'key', 'page'}
    assert app.chat_input[0].disabled and not buttons(app, 'v2')
    app.button[0].click().run(timeout=10)
    assert not app.session_state.v2_state.door_open and len(buttons(app, 'v2')) == 3
