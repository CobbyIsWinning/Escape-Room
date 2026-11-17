"""Typed wizard dialogue and opt-in model-generated speech for both apps."""
import hashlib
from pathlib import Path
import re
import uuid

import streamlit as st
import streamlit.components.v1 as components

from shared.config import INTRO
from shared.llm import api_key
from shared.scenery import WAKE_SECONDS
from shared.speech import generate_speech

wizard_component = components.declare_component(
    'wizard_dialogue', path=str(Path(__file__).resolve().parent / 'ui'),
)


def spoken_text(content):
    dialogue = content.partition('\n\n**Library event:** ')[0]
    if dialogue == INTRO and '“' in dialogue:
        dialogue = dialogue.split('“', 1)[1].rstrip('”')
    dialogue = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', dialogue)
    return re.sub(r'[*_`#]', '', dialogue).strip()



def reset_dialogue(prefix):
    st.session_state.pop(prefix + '_dialogue', None)


def _state(prefix):
    key = prefix + '_dialogue'
    if key not in st.session_state:
        st.session_state[key] = {
            'game': uuid.uuid4().hex, 'shown': set(), 'audio': {}, 'attempted': set(),
        }
    return st.session_state[key]


def read_aloud_control(prefix):
    return st.toggle('Read aloud · magical voice', key=prefix + '_voice',
                     help='Hear Morvan in an AI-generated wizard voice. Audio controls let you pause or replay.')


def wizard_message(content, *, prefix, index, latest, voice_enabled):
    state = _state(prefix)
    identity = hashlib.sha256(f'{state["game"]}:{index}:{content}'.encode()).hexdigest()[:16]
    dialogue, separator, event = content.partition('\n\n**Library event:** ')
    if latest:
        animate = identity not in state['shown']
        timing = st.session_state.get(prefix + '_scenery', {})
        if index == 0 and timing:
            import time
            delay = max(0, WAKE_SECONDS - (time.monotonic() - timing['woke_at']))
        else:
            delay = 0
        wizard_component(text=dialogue, identity=identity, animate=animate,
                         delay_ms=int(delay * 1000), key=f'{prefix}_type_{identity}', default=None)
        state['shown'].add(identity)
        if separator:
            st.markdown('**Library event:** ' + event)
        with st.expander('Read transcript'):
            st.write(content)
        _voice(content, identity, state, prefix, voice_enabled)
    else:
        st.write(content)


def _voice(content, identity, state, prefix, enabled):
    replay = st.button('🔊 Hear the wizard', key=f'{prefix}_hear_{identity}',
                       help='Generate or replay this reply in Morvan’s magical voice.')
    requested = replay or (enabled and identity not in state['attempted'])
    autoplay = False
    if requested and identity not in state['audio']:
        state['attempted'].add(identity)
        if not api_key():
            st.info('Add a Gemini API key to hear the wizard. You can keep reading the dialogue.')
        else:
            try:
                with st.spinner('Morvan’s voice takes shape…'):
                    state['audio'][identity] = generate_speech(spoken_text(content))
                autoplay = True
            except Exception:
                st.info('Morvan’s voice is unavailable for the moment. Keep reading, or tap “Hear the wizard” to try again.')
    if identity in state['audio']:
        st.audio(state['audio'][identity], format='audio/wav', autoplay=autoplay or replay,
                 alt='Morvan’s AI-generated wizard voice')
        st.caption('AI-generated voice · Use the player to pause or replay.')
