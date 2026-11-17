"""Wizard-library scenery, a browser-driven idle slideshow, and waking mist."""
from base64 import b64encode
from html import escape
from mimetypes import guess_type
from pathlib import Path

import streamlit as st

from shared.scenery import IDLE_SECONDS, WAKE_SECONDS, scene_timing

CLOUD_PIN = 'https://www.pinterest.com/pin/574209021262662947/'
CLOUD_VIDEO = Path(__file__).resolve().parents[1] / 'assets' / 'cloudy-opening.mp4'

SCENES = (
    ('pinterest-candlelit.jpg', 'The veiled rotunda', 'Light pierces the haze. Somewhere, a lock turns.',
     'Pinterest preview', 'https://i.pinimg.com/736x/01/22/f2/0122f24f68d6d7b25b502ec21f3be75a.jpg'),
    ('pinterest-gallery.jpg', 'The whispering gallery', 'Old shelves shift beneath the wizard’s gaze.',
     'Pinterest preview', 'https://i.pinimg.com/736x/a9/e6/fb/a9e6fb7f8eeba54337cbf4cc81ed10a5.jpg'),
    ('pinterest-archive.jpg', 'The enchanted archive', 'Candlelight gathers where the spell grows thin.',
     'Pinterest preview', 'https://i.pinimg.com/736x/8d/e5/0c/8de50c330437ce40af93d343966a0962.jpg'),
    ('pinterest-study.jpg', 'The wizard’s study', 'Beyond the ancient glass, daylight is waiting.',
     'Pinterest preview', 'https://i.pinimg.com/736x/28/d5/64/28d56496268b4b3777a8540b30a1f624.jpg'),
)


@st.cache_data(show_spinner=False)
def image_url(filename):
    path = Path(__file__).resolve().parents[1] / 'assets' / filename
    mime_type = guess_type(filename)[0] or 'application/octet-stream'
    return f'data:{mime_type};base64,' + b64encode(path.read_bytes()).decode('ascii')


def library_background(key, stage):
    age, awake_age = scene_timing(st.session_state, key, stage)
    scene_index = min(stage, len(SCENES) - 1)
    background = image_url(SCENES[scene_index][0])
    cloud_poster = image_url('cloudy-opening.jpg')
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
        [class*="st-key-wake_opening_"] {{ position: fixed !important; inset: 0; z-index: 9999;
            width: 100% !important; height: 100% !important; overflow: hidden;
            pointer-events: none; background: #080e19 url("{cloud_poster}") center / cover;
            animation: wake-reveal {WAKE_SECONDS}s ease-in-out {-awake_age}s forwards; }}
        [class*="st-key-wake_opening_"] video {{ position: absolute; inset: 0; width: 100%;
            height: 100%; object-fit: cover; pointer-events: none; }}
        [class*="st-key-wake_opening_"] video::-webkit-media-controls {{ display: none !important; }}
        .wake-fog {{ position: fixed; inset: 0; z-index: 2; pointer-events: none;
            background: linear-gradient(rgba(8, 14, 25, .08), rgba(8, 14, 25, .3));
            display: grid; place-items: center; }}
        .wake-fog p {{ color: #edf4ff; font: italic clamp(1.3rem, 4vw, 2rem) Georgia, serif;
            text-shadow: 0 2px 24px #000; text-align: center; padding: 1.5rem; z-index: 1; }}
        .wake-cloud {{ position: absolute; inset: -30%; filter: blur(28px); opacity: .3;
            background: radial-gradient(ellipse at 22% 40%, #e9eff0 0%, transparent 52%),
                radial-gradient(ellipse at 78% 60%, #8e9ba7 0%, transparent 50%);
            animation: cloud-drift {WAKE_SECONDS}s ease-out {-awake_age}s both; }}
        @keyframes library-cycle {{
            0% {{ opacity: 0; }} 1.11%, 25% {{ opacity: 1; }}
            26.11%, 100% {{ opacity: 0; }}
        }}
        @keyframes wake-reveal {{
            0%, 50% {{ opacity: 1; visibility: visible; }}
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
            [class*="st-key-wake_opening_"], .wake-fog, .wake-cloud {{ display: none !important; }}
        }}
    </style>''', unsafe_allow_html=True)
    if awake_age < WAKE_SECONDS:
        # A fresh node resumes the CSS timeline correctly on reruns and restarts.
        woke_at = st.session_state[key]['woke_at']
        opening_key = f'wake_opening_{int(woke_at * 1_000_000)}_{int(awake_age * 1_000_000)}'
        with st.container(key=opening_key):
            st.video(str(CLOUD_VIDEO), autoplay=True, muted=True, loop=True,
                     start_time=int(awake_age), alt='Starry sky seen through trees, from the opening Pinterest Pin')
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
    with st.expander('Library artwork · Pinterest'):
        st.caption('[Ancient library search on Pinterest](https://www.pinterest.com/search/pins/?q=ancient%20library&rs=typed)')
        for _, title, _, source, source_url in SCENES:
            st.caption(f'[{title} — {source}]({source_url})')
        st.caption(f'[Starry awakening video — Pinterest Pin]({CLOUD_PIN})')
        st.caption('Public preview images, preserved as supplied.')
