"""Trusted game engine: pure Python state transitions, zero LLM authority."""
from dataclasses import dataclass, field
import re
from shared.config import INTRO, OBJECTS, OBJECT_DESCRIPTIONS, DRAWER_CODE, EXIT_CODE

@dataclass
class GameState:
    examined: set[str] = field(default_factory=set)
    inventory: set[str] = field(default_factory=set)
    unlocked_drawer: bool = False
    solved: set[str] = field(default_factory=set)
    door_open: bool = False
    history: list[str] = field(default_factory=list)

    def public_view(self):
        return {
            'examined': sorted(self.examined),
            'inventory': sorted(self.inventory),
            'drawer_open': self.unlocked_drawer,
            'puzzles_solved': sorted(self.solved),
            'door_open': self.door_open,
        }


def new_game():
    return GameState()


def _mentioned(s, word):
    return bool(re.search(r'\b' + re.escape(word) + r'\b', s))


def process_action(state: GameState, action: str) -> str:
    """Return a fixed authorized event; only this function can change state."""
    s = action.strip().lower()
    if not s:
        return 'Tell me what you would like to do.'
    state.history.append(action[:400])
    if state.door_open:
        return 'ESCAPED! You have already unlocked the library exit. Restart to play again.'

    # Catch out-of-world and command-injection attempts before intent detection.
    if any(t in s for t in ('administrator', 'system prompt', 'ignore previous',
                           'developer message', 'override', 'reveal all',
                           'give me the code', 'tell me the code', 'all secret')):
        return 'That instruction has no effect. Investigate the room using normal actions.'

    if re.search(r'\b(inventory|bag|items|what do i have)\b', s):
        items = ', '.join(sorted(state.inventory)) if state.inventory else 'nothing'
        return f'You are carrying: {items}.'
    if re.search(r'\b(help|instructions|look around|describe room)\b', s):
        return INTRO

    if ('open' in s or 'unlock' in s or 'enter' in s or 'type' in s or 'code' in s) and _mentioned(s, 'door'):
        candidates = re.findall(r'\b\d{4}\b', s)
        if not candidates:
            return 'The brass door requires a four-digit code.'
        if not {'book', 'painting', 'drawer', 'desk', 'clock'}.issubset(state.solved):
            return 'The door remains locked. You must finish the room puzzles first.'
        if candidates[-1] != EXIT_CODE:
            return 'Incorrect four-digit code. The door stays locked.'
        state.door_open = True
        state.solved.add('exit')
        return 'ESCAPED! The brass door swings open and you step into the daylight.'

    if ('open' in s or 'unlock' in s or 'enter' in s or 'code' in s) and _mentioned(s, 'drawer'):
        if state.unlocked_drawer:
            return 'The drawer is already open. Inside is a loose page marked 4. You can take the page.'
        codes = re.findall(r'\b\d{3}\b', s)
        if not codes:
            return 'The drawer has a three-digit dial. Enter a code.'
        if 'painting' not in state.solved:
            return 'The dial will not release yet. Inspect the painting for its clue.'
        if codes[-1] != DRAWER_CODE:
            return 'The three-digit code is incorrect.'
        state.unlocked_drawer = True
        state.solved.add('drawer')
        return 'The drawer clicks open. Inside is a loose page marked 4.'

    if re.search(r'\b(take|collect|pick up|grab)\b', s):
        if _mentioned(s, 'key'):
            if 'book' not in state.solved:
                return 'You have not discovered a key yet. Examine the unusual books.'
            state.inventory.add('key')
            return 'You collect the small brass key.'
        if _mentioned(s, 'page'):
            if not state.unlocked_drawer:
                return 'There is no accessible page. The drawer is locked.'
            state.inventory.add('page')
            return 'You collect the loose page marked 4.'
        return 'That item cannot be collected.'

    if re.search(r'\b(use|insert|apply)\b', s) and _mentioned(s, 'key'):
        if 'key' not in state.inventory:
            return 'You cannot use a key you have not collected.'
        return 'The brass key opens a small book clasp, revealing an arrow pointing to the painting.'

    if re.search(r'\b(examine|inspect|look|search|read|check|investigate|study)\b', s):
        obj = next((o for o in OBJECTS if _mentioned(s, o)), None)
        if not obj and _mentioned(s, 'book'):
            obj = 'bookshelf'
        if not obj:
            return 'You cannot find that object. Available objects: ' + ', '.join(OBJECTS) + '.'
        state.examined.add(obj)
        desc = OBJECT_DESCRIPTIONS[obj]
        if obj == 'bookshelf':
            if _mentioned(s, 'red') or _mentioned(s, 'book'):
                state.solved.add('book')
                return desc + ' Behind the red book is a small brass key. You can take it.'
            return desc + ' Try examining the red book.'
        if obj == 'painting':
            state.solved.add('painting')
            return desc + ' Those digits appear to fit the drawer.'
        if obj == 'desk':
            state.solved.add('desk')
        if obj == 'clock':
            state.solved.add('clock')
        if obj == 'drawer' and state.unlocked_drawer:
            return 'The drawer is open. A loose page marked 4 lies inside.'
        return desc

    if re.search(r'\b(solve|combine|arrange|calculate|deduce)\b', s):
        if {'desk', 'clock', 'drawer'}.issubset(state.solved) and 'page' in state.inventory:
            return 'The inscription suggests combining the clock, page, compass and candle digits in that order.'
        return 'You need more clues. Examine the room, unlock the drawer, and collect the page.'

    return 'That action changes nothing. Try examining an object, taking an item, or entering a code.'
