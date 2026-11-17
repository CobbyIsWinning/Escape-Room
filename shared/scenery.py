"""Presentation-only scene progress and timing; never authorizes game actions."""
import re
import time

IDLE_SECONDS = 45
WAKE_SECONDS = 6


def scene_timing(session, key, stage, *, now=None):
    """Keep idle time across reruns; reset it only when the puzzle stage changes."""
    now = time.monotonic() if now is None else now
    state = session.get(key)
    if state is None:
        state = {'stage': stage, 'since': now, 'woke_at': now}
        session[key] = state
    elif state['stage'] != stage:
        state['stage'] = stage
        state['since'] = now
    return max(0, now - state['since']), max(0, now - state['woke_at'])


def stage_for_state(state):
    """Use only the trusted engine's completed milestones in Version 2."""
    if state.door_open:
        return 4
    if state.unlocked_drawer:
        return 3
    if 'painting' in state.solved:
        return 2
    if 'book' in state.solved:
        return 1
    return 0


def stage_for_reply(reply, current=0):
    """Version 1 has no trusted state: its wizard's prose only directs the visuals."""
    text = reply.lower()
    if 'escaped!' in text:
        return 4
    if re.search(r'drawer.{0,35}(clicks open|swings open|opens|unlocks)|loose page|page marked', text):
        return max(current, 3)
    if '314' in text or re.search(r'3\s*[-–,]\s*1\s*[-–,]\s*4', text):
        return max(current, 2)
    if re.search(r'(find|found|discover|behind|collect|reveal|take).{0,90}\bkey\b', text):
        return max(current, 1)
    return current
