# AI-Powered Escape Room — Mini Project 01

Two Streamlit applications matching the assignment, plus diagrams, tests and a short report.

## Install and run

```bash
cd AI_Escape_Room
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
export GEMINI_API_KEY='YOUR_API_KEY'  # Windows PowerShell: $env:GEMINI_API_KEY='...'
streamlit run version1/app.py
# Separate terminal, from project root:
streamlit run version2/app.py --server.port 8502
```

To get a key, use Google AI Studio. Free-tier usage depends on Google's current eligibility, limits and quotas. The default model is `gemini-3.8-flash`; set `GEMINI_MODEL` to an available alternative if necessary. Do **not** commit the key. Version 1 needs an API key for gameplay. Version 2 runs fully offline for validated gameplay; a key enables optional narration. `streamlit` runs on the local machine. `pytest` requires no LLM or network.

## Puzzle walkthrough (spoilers)

Both versions open with a six-second cloudy awakening. Morvan, the wizard who
locked you in the library, speaks through the chat. Four locally stored Zedge
previews change at clue milestones and crossfade every 45 seconds without
progress. Ordinary chat reruns preserve the idle timer. “Wake again” resets the
game and replays the opening; reduced-motion preferences skip the mist animation.
The library settles on the sunlit study when the player escapes. Image sources
and artist credits are in `assets/README.md` and the in-app artwork expander.
Version 1 chooses visual milestones from the wizard's prose; Version 2 uses
only trusted puzzle state. The idle animation makes no API calls.

1. `examine red book` -> discover key; `take key`.
2. `examine painting` -> see `314`; `open drawer with 314` -> page `4`.
3. `take page`; `examine desk` and `examine clock` -> order clock/page/compass/candle = `7-4-2-6`.
4. `open door with 7426` -> ESCAPED.

At least six room objects are interactive: bookshelf, painting, desk, clock, drawer and door. Version 2 recognizes these and intentionally restricts the world to them.

## Technical differences

- Version 1: UI -> full chat -> Gemini -> reply. The model sees solutions and judges actions; it can make mistakes or be tricked. No independent game-state checks. This is **intentional** for comparison.
- Version 2: UI -> Python intent parsing and action validator -> structured `GameState` -> authorized event -> UI and optional Gemini narration. The model never writes to `GameState`. Public state is shown in a sidebar.
- Version 2 tests verify eight cases, including key-before-pickup, wrong drawer code, false solved-puzzle claim, administrator impersonation, code disclosure request, nonexistent object, premature correct door code, and legitimate completion.

## Caveats

Version 2 uses a small, rule-based language parser rather than a general NLP intent model, so not every natural-language paraphrase is supported. The Gemini narration is explicitly labeled non-authoritative and may still hallucinate prose; the displayed authorized event and state remain correct. Version 1 failure examples in the report are **risks and test prompts**, not fabricated empirical observations from a live model run.

## Tests

```bash
python -m pytest -q
```

## Files

- `version1/app.py`: LLM-controlled version
- `version2/engine.py`: deterministic engine and validator
- `version2/app.py`: safer Streamlit UI, optional narration
- `shared/config.py`: room/puzzle settings
- `shared/llm.py`: Google Gemini wrapper
- `shared/appearance.py`: library scenes, image credits, and waking mist
- `shared/scenery.py`: presentation-only milestone and idle timing
- `tests/test_engine.py`: regression tests
- `diagrams/`: architecture diagrams in SVG and PNG
- `Mini_Project_Report.pdf`: 2–3-page report
