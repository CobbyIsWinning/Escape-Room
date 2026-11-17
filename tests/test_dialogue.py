"""Narration keeps exact text, escapes scripts, and never repeats speech requests."""
from io import BytesIO
from pathlib import Path
import wave

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from shared import dialogue, llm
from shared.config import INTRO
from shared.speech import SpeechUnavailable, enchanted_wave


def test_transcript_keeps_puzzle_event_out_of_wizards_spoken_line():
    assert dialogue.spoken_text('“A clever move.”\n\n**Library event:** Secret result.') == '“A clever move.”'
    greeting = dialogue.spoken_text(INTRO)
    assert greeting.startswith('Awake at last.')
    assert 'Silver mist clouds your vision' not in greeting


def test_wizard_echo_is_valid_mono_audio_with_a_short_tail():
    pcm = np.array([32767, -32768] * 1200, dtype='<i2').tobytes()
    audio = enchanted_wave(pcm)
    with wave.open(BytesIO(audio), 'rb') as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 24000
        assert wav.getnframes() == 2400 + int(.32 * 24000)
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
        assert np.max(np.abs(samples.astype(np.int32))) <= 32767
        assert np.any(samples[2400:] != 0)
    with pytest.raises(SpeechUnavailable):
        enchanted_wave(b'')


def test_read_aloud_is_opt_in_and_cached_across_reruns(monkeypatch):
    calls = []

    def voice(text):
        calls.append(text)
        return enchanted_wave(np.zeros(240, dtype='<i2').tobytes())

    monkeypatch.setattr(dialogue, 'api_key', lambda: 'test-only')
    monkeypatch.setattr(dialogue, 'generate_speech', voice)
    monkeypatch.setattr(llm, 'api_key', lambda: 'test-only')
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'version1/app.py')).run(timeout=10)
    assert not app.exception
    assert calls == []
    app.toggle[0].set_value(True).run(timeout=10)
    assert not app.exception
    assert len(calls) == 1
    shown = set(app.session_state.v1_dialogue['shown'])
    app.run(timeout=10)
    assert len(calls) == 1
    assert app.session_state.v1_dialogue['shown'] == shown
    app.toggle[0].set_value(False).run(timeout=10)
    app.button(key=next(button.key for button in app.button if button.label == '🔊 Hear the wizard')).click().run(timeout=10)
    assert not app.exception
    assert len(calls) == 1


def test_speech_failure_keeps_gameplay_and_does_not_retry_on_every_rerun(monkeypatch):
    calls = []

    def unavailable(text):
        calls.append(text)
        raise SpeechUnavailable('Temporarily unavailable')

    monkeypatch.setattr(dialogue, 'api_key', lambda: 'test-only')
    monkeypatch.setattr(dialogue, 'generate_speech', unavailable)
    monkeypatch.setattr(llm, 'api_key', lambda: '')
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'version2/app.py')).run(timeout=10)
    app.toggle[0].set_value(True).run(timeout=10)
    assert not app.exception
    assert len(calls) == 1
    app.run(timeout=10)
    assert len(calls) == 1
    assert not app.session_state.v2_state.door_open
    assert not app.chat_input[0].disabled
