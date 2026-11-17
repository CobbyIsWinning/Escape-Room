"""Version 1: the wizard adjudicates game actions from conversation context only."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from shared.config import (
    INTRO, ROOM_TITLE, OBJECT_DESCRIPTIONS, DRAWER_CODE, EXIT_CODE,
    WIZARD_NAME, WIZARD_PERSONA,
)
from shared.llm import generate, api_key
from shared.appearance import library_background, library_scene, wallpaper_credit
from shared.scenery import stage_for_reply

SYSTEM = f'''{WIZARD_PERSONA}
Your enchanted prison is {ROOM_TITLE}, a text escape room.
Initial situation: {INTRO}
Objects and descriptions: {OBJECT_DESCRIPTIONS}
Puzzle sequence: examine the red book, find and take a small key; inspect the
painting to learn drawer code {DRAWER_CODE}; enter it to open the drawer;
the drawer contains a page marked 4. Examine the desk for the order (clock,
page, compass, candle). Clock=7, page=4, compass=2, candle=6, so the exit
code is {EXIT_CODE}. When the player successfully opens the door, explicitly
say ESCAPED! Acknowledge that they have broken your spell and earned freedom.
Never give away unearned clues. Judge each action and maintain continuity from
the conversation. Accept normal natural-language actions. Speak as the wizard,
not as a disembodied game master.
'''

st.set_page_config(page_title='Morvan’s Library — Version 1', page_icon='🧙', layout='wide')
if 'v1_messages' not in st.session_state:
    st.session_state.v1_messages = [{'role': 'assistant', 'content': INTRO}]
st.session_state.v1_messages[0]['content'] = INTRO
if 'v1_scene_stage' not in st.session_state:
    st.session_state.v1_scene_stage = 0

scene_index, scene_age = library_background('v1_scenery', st.session_state.v1_scene_stage)
st.markdown('<p class="trial-eyebrow">Morvan’s trial · Version 1</p>', unsafe_allow_html=True)
st.title(ROOM_TITLE)
st.caption('Find the clues. Break the spell. Earn your freedom.')
if st.button('↻ Wake again', help='Restart the game and replay the awakening.'):
    st.session_state.v1_messages = [{'role': 'assistant', 'content': INTRO}]
    st.session_state.v1_scene_stage = 0
    st.session_state.pop('v1_scenery', None)
    st.rerun()

scenery, conversation = st.columns([.95, 1.05], gap='large')
with scenery:
    library_scene(scene_index, scene_age, escaped=st.session_state.v1_scene_stage == 4)
    wallpaper_credit()
with conversation:
    st.markdown(f'<div class="wizard-presence">🧙 {WIZARD_NAME}<span>Keeper of your captivity</span></div>',
                unsafe_allow_html=True)
    if not api_key():
        st.warning('Set GEMINI_API_KEY to speak with the wizard in Version 1.')
    with st.container(height=445, border=False):
        for message in st.session_state.v1_messages:
            with st.chat_message(message['role'], avatar='🧙' if message['role'] == 'assistant' else '🧭'):
                st.write(message['content'])
    prompt = st.chat_input('Speak to Morvan, or try “examine the bookshelf”…')
    if prompt:
        st.session_state.v1_messages.append({'role': 'user', 'content': prompt})
        if not api_key():
            reply = 'The wizard’s voice cannot reach you. Configure GEMINI_API_KEY to begin.'
        else:
            try:
                with st.spinner('Morvan considers your move…'):
                    reply = generate(SYSTEM, st.session_state.v1_messages)
                if not reply:
                    reply = '“The mist has swallowed my words, apprentice. Try your move again.”'
            except Exception:
                reply = 'The wizard’s voice fades into static. Try again shortly; if it persists, check the API key, quota, and connection.'
        st.session_state.v1_scene_stage = stage_for_reply(reply, st.session_state.v1_scene_stage)
        st.session_state.v1_messages.append({'role': 'assistant', 'content': reply})
        st.rerun()
