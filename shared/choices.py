"""Three player replies per turn; suggestions never authorize a game action."""
import json
import re

from shared.config import DRAWER_CODE, EXIT_CODE

OPENING_OPTIONS = ('Examine the bookshelf', 'Inspect the painting', 'Examine the desk')

TURN_SCHEMA = {
    'type': 'object',
    'properties': {
        'dialogue': {
            'type': 'string',
            'description': 'Morvan’s spoken reply in two or three short sentences. Do not list the response options here.',
        },
        'options': {
            'type': 'array', 'minItems': 3, 'maxItems': 3,
            'items': {'type': 'string'},
            'description': 'Exactly three distinct short replies the player can choose next, written from the player’s perspective. Match the wizard’s question or current scene. Use actions or answers, not narration. Do not reveal unearned clues, solutions, or items. The player may also type freely.',
        },
    },
    'required': ['dialogue', 'options'],
    'additionalProperties': False,
}


def fallback_options(reply):
    """Version 1 fallback follows public prose, without inventing a trusted state."""
    text = reply.lower()
    if 'loose page' in text or re.search(r'drawer.{0,30}(opens|clicks open)', text):
        return ('Take the page', 'Examine the desk', 'Examine the clock')
    if re.search(r'(find|found|discover|behind|collect|reveal).{0,90}\bkey\b', text):
        return ('Take the key', 'Inspect the painting', 'Examine the clock')
    return OPENING_OPTIONS


def parse_turn(response):
    """Read a structured reply, accepting plain prose if a provider omits JSON."""
    text = (response or '').strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.IGNORECASE)
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        if text.startswith(('{', '[')):
            text = '“The mist has swallowed my words, apprentice. Try your move again.”'
        return text, fallback_options(text)
    if not isinstance(data, dict) or not isinstance(data.get('dialogue'), str):
        reply = '“The mist has swallowed my words, apprentice. Try your move again.”'
        return reply, OPENING_OPTIONS
    reply = data['dialogue'].strip()
    valid, seen = [], set()
    options = data.get('options', [])
    for item in options if isinstance(options, list) else []:
        if not isinstance(item, str):
            continue
        item = ' '.join(item.split())
        if item and len(item) <= 120 and item.casefold() not in seen:
            valid.append(item)
            seen.add(item.casefold())
    for item in fallback_options(reply):
        if len(valid) >= 3:
            break
        if item.casefold() not in seen:
            valid.append(item)
            seen.add(item.casefold())
    return reply, tuple(valid[:3])


def _code_options(code, target):
    return tuple(f'Open {target} with {answer}' for answer in
                 (code[::-1], code, code[1] + code[0] + code[2:]))


def choices_for_state(state):
    """Only earned facts from Python state can appear in Version 2's answers."""
    if state.door_open:
        return ()
    if 'book' not in state.solved:
        if 'bookshelf' in state.examined:
            return ('Examine the red book', 'Inspect the painting', 'Examine the clock')
        return OPENING_OPTIONS
    if 'key' not in state.inventory:
        return ('Take the key', 'Inspect the painting', 'Examine the clock')
    if 'painting' not in state.solved:
        return ('Inspect the painting', 'Use key on the book clasp', 'Examine the desk')
    if not state.unlocked_drawer:
        return _code_options(DRAWER_CODE, 'drawer')
    if 'page' not in state.inventory:
        return ('Take the page', 'Examine the desk', 'Examine the clock')
    if 'desk' not in state.solved:
        return ('Examine the desk', 'Examine the clock', 'Check inventory')
    if 'clock' not in state.solved:
        return ('Examine the clock', 'Read the desk', 'Check inventory')
    return _code_options(EXIT_CODE, 'door')


def response_options(options, *, prefix, turn, disabled=False):
    """A click submits exactly the displayed reply through the normal action path."""
    import streamlit as st
    if not options:
        return None
    selected = None
    with st.container(key=prefix + '_response_options'):
        st.caption('Choose your response')
        for index, option in enumerate(options):
            if st.button(f'{chr(65 + index)} · {option}', key=f'{prefix}_reply_{turn}_{index}',
                         width='stretch', disabled=disabled):
                selected = option
    return selected
