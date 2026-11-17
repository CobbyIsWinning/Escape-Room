"""Gemini wizard speech and a restrained library echo. Credentials stay server-side."""
from io import BytesIO
import os
import re
import wave

import numpy as np

from shared.llm import api_key


class SpeechUnavailable(RuntimeError):
    """Speech is unavailable; the written dialogue remains usable."""


def enchanted_wave(pcm, rate=24000):
    """Wrap 16-bit mono PCM in a WAV, adding a quiet, short echo without clipping."""
    if not pcm or len(pcm) % 2:
        raise SpeechUnavailable('The speech service returned invalid audio.')
    samples = np.frombuffer(pcm, dtype='<i2').astype(np.float32)
    echoes = ((.09, .11), (.19, .07), (.32, .04))
    output = np.zeros(len(samples) + int(rate * echoes[-1][0]), dtype=np.float32)
    output[:len(samples)] = samples * .86
    for seconds, strength in echoes:
        offset = int(seconds * rate)
        output[offset:offset + len(samples)] += samples * strength
    peak = float(np.max(np.abs(output)))
    if peak > 32767:
        output *= 32767 / peak
    buffer = BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(output.astype('<i2').tobytes())
    return buffer.getvalue()


def generate_speech(text):
    """Read the supplied spoken dialogue verbatim; speech never changes game state."""
    key = api_key()
    if not key:
        raise SpeechUnavailable('Add a Gemini API key to hear Morvan’s voice.')
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key, http_options=types.HttpOptions(
        timeout=30000, retry_options=types.HttpRetryOptions(attempts=1),
    ))
    response = client.models.generate_content(
        model=os.getenv('GEMINI_TTS_MODEL', 'gemini-3.1-flash-tts-preview'),
        contents=(
            'Generate a spoken performance of the following transcript. '
            'Voice: a mature, low, slightly gravelly wizard, quietly amused and mysterious. '
            'Delivery: theatrical fantasy storytelling, unhurried but natural, with soft '
            'breath and deliberate pauses. Do not sing or shout. '
            'Read the transcript verbatim; do not add words or read these directions.\n\n'
            'TRANSCRIPT:\n' + text
        ),
        config=types.GenerateContentConfig(
            response_modalities=['AUDIO'],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Algenib'),
            )),
        ),
    )
    chunks = []
    rate = 24000
    for candidate in response.candidates or []:
        if not candidate.content:
            continue
        for part in candidate.content.parts or []:
            inline = part.inline_data
            if inline and inline.data and (inline.mime_type or '').startswith('audio/'):
                chunks.append(inline.data)
                match = re.search(r'rate=(\d+)', inline.mime_type or '')
                if match:
                    rate = int(match[1])
        if chunks:
            break
    if not chunks:
        raise SpeechUnavailable('Morvan’s voice is quiet for the moment. Try again shortly.')
    return enchanted_wave(b''.join(chunks), rate)
