"""Wizard-library scenery, a browser-driven idle slideshow, and waking mist."""
from base64 import b64encode
from html import escape
from pathlib import Path

import streamlit as st

from shared.scenery import IDLE_SECONDS, WAKE_SECONDS, scene_timing

SCENES = (
    ('ancient-library.webp', 'The candlelit stacks', 'A candle burns. Somewhere, a lock turns.',
     'ShutterCraft Studios', 'b6379b5a-5cb5-4b1e-81f6-de12b30bf680'),
    ('gothic-library.webp', 'The whispering gallery', 'Old shelves shift beneath the wizard’s gaze.',
     'emowls83', '5f539b31-752a-40cc-b202-64171cff3e66'),
    ('enchanted-library.webp', 'The enchanted archive', 'Blue light gathers where the spell grows thin.',
     'MistressBellaJean', '91d1a854-12da-4ac0-b97e-fd7ebc0a244b'),
    ('wizard-library.webp', 'The wizard’s study', 'Beyond the ancient glass, daylight is waiting.',
     'AvianGrace', '5837f049-7190-412b-b1b5-08645d69cff0'),
)


@st.cache_data(show_spinner=False)
def image_url(filename):
    path = Path(__file__).resolve().parents[1] / 'assets' / filename
    return 'data:image/webp;base64,' + b64encode(path.read_bytes()).decode('ascii')


def library_background(key, stage):
    age, awake_age = scene_timing(st.session_state, key, stage)
    scene_index = min(stage, len(SCENES) - 1)
    background = image_url(SCENES[scene_index][0])
    st.markdown(f'''<style>
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(rgba(12, 10, 8, .83), rgba(12, 10, 8, .94)),
                url("{background}") center / cover fixed;
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stMainBlockContainer"] {{
            max-width: 1200px; padding: 2.5rem 2rem 2rem;
        }}
        [data-testid="stSidebar"] {{ background: #17130f; }}
        [data-testid="stChatMessage"] {{
            background: rgba(37, 31, 24, .9);
            border: 1px solid rgba(213, 174, 115, .12); border-radius: 14px;
        }}
        h1 {{ font-family: Georgia, serif; letter-spacing: -.035em; }}
        .trial-eyebrow {{ color: #d5ae73; letter-spacing: .23em; font-size: .7rem;
            text-transform: uppercase; margin: 0 0 .5rem; }}
        .library-scene {{ position: relative; height: 545px; overflow: hidden;
            margin: 0; border-radius: 18px; isolation: isolate;
            background: #17130f; border: 1px solid #5e4930; }}
        .scene-frame {{ position: absolute; inset: 0; opacity: 0;
            background-size: cover; background-position: center;
            animation: library-cycle {len(SCENES) * IDLE_SECONDS}s linear infinite; }}
        .scene-frame::after {{ content: ''; position: absolute; inset: 0;
            background: linear-gradient(180deg, rgba(7, 7, 10, .12) 45%, rgba(7, 7, 10, .93)); }}
        .scene-caption {{ position: absolute; left: 1.5rem; right: 1.5rem;
            bottom: 1.5rem; z-index: 1; }}
        .scene-caption h2 {{ font: 1.8rem/1.15 Georgia, serif; color: #f7ead4;
            padding: 0; margin: .5rem 0; }}
        .scene-caption p {{ color: #dbd0bf; font-size: .85rem; margin: 0; }}
        .scene-caption small, .scene-label {{ font-size: .63rem; letter-spacing: .15em;
            text-transform: uppercase; color: #e0c395; }}
        .scene-label {{ position: absolute; z-index: 5; top: 1.25rem; left: 1.25rem;
            background: rgba(13, 11, 9, .75); border: 1px solid #6b5334;
            padding: .5rem .7rem; border-radius: 20px; }}
        .wizard-presence {{ padding: .65rem 0 1rem; color: #dfc393;
            font-family: Georgia, serif; font-size: 1.1rem; }}
        .wizard-presence span {{ font: .72rem sans-serif; color: #b1a592;
            margin-left: .5rem; }}
        .wake-fog {{ position: fixed; inset: 0; z-index: 9999; pointer-events: none;
            background: #c0c8cb; display: grid; place-items: center;
            animation: wake-reveal {WAKE_SECONDS}s ease-in-out {-awake_age}s forwards; }}
        .wake-fog p {{ color: #262e38; font: italic clamp(1.3rem, 4vw, 2rem) Georgia, serif;
            text-align: center; padding: 1.5rem; z-index: 1; }}
        .wake-cloud {{ position: absolute; inset: -30%; filter: blur(28px);
            background: radial-gradient(ellipse at 22% 40%, #e9eff0 0%, transparent 52%),
                radial-gradient(ellipse at 78% 60%, #8e9ba7 0%, transparent 50%);
            animation: cloud-drift {WAKE_SECONDS}s ease-out {-awake_age}s both; }}
        @keyframes library-cycle {{
            0% {{ opacity: 0; }} 1.11%, 25% {{ opacity: 1; }}
            26.11%, 100% {{ opacity: 0; }}
        }}
        @keyframes wake-reveal {{
            0%, 20% {{ opacity: 1; visibility: visible; }}
            100% {{ opacity: 0; visibility: hidden; }}
        }}
        @keyframes cloud-drift {{
            from {{ transform: scale(1) translateX(-5%); }}
            to {{ transform: scale(1.5) translateX(14%); }}
        }}
        @media (max-width: 700px) {{
            [data-testid="stMainBlockContainer"] {{ padding: 1.5rem 1rem; }}
            .library-scene {{ height: 320px; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .wake-fog, .wake-cloud {{ display: none; }}
        }}
    </style>''', unsafe_allow_html=True)
    if awake_age < WAKE_SECONDS:
        st.markdown('''<div class="wake-fog" aria-hidden="true"><div class="wake-cloud"></div>
            <p>A clouded mind. A locked door.<br>Someone is waiting for you to wake.</p></div>''',
            unsafe_allow_html=True)
    return scene_index, age


def library_scene(scene_index, age, *, escaped=False):
    frames = []
    for offset in range(len(SCENES)):
        filename, title, description, _, _ = SCENES[(scene_index + offset) % len(SCENES)]
        delay = offset * IDLE_SECONDS - age % (len(SCENES) * IDLE_SECONDS) - 2
        animation = f'animation-delay:{delay:.3f}s;'
        if escaped:
            animation = f'animation:none;opacity:{1 if offset == 0 else 0};'
        frames.append(f'''<div class="scene-frame" style="background-image:url('{image_url(filename)}');{animation}">
            <div class="scene-caption"><small>{'The spell is broken' if escaped else 'Within Morvan’s spell'}</small>
            <h2>{escape(title)}</h2><p>{escape(description)}</p></div></div>''')
    st.markdown(f'''<figure class="library-scene" aria-label="Enchanted library scenery">
        {''.join(frames)}<div class="scene-label">{'✦ You are free' if escaped else '✦ The library is watching'}</div>
        </figure>''', unsafe_allow_html=True)
    st.caption('The spell changes the view as you discover clues, or linger for 45 seconds.')


def wallpaper_credit():
    with st.expander('Library artwork · Zedge'):
        for _, title, _, artist, item_id in SCENES:
            st.caption(f'[{title} — {artist}](https://www.zedge.net/wallpapers/{item_id})')
        st.caption('Public previews, preserved as supplied, including any watermarks.')
