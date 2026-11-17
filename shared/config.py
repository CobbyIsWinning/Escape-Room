"""Canonical puzzle design. Never pass secret solutions to the Version 2 narrator."""
ROOM_TITLE = 'The Clockwork Library'
WIZARD_NAME = 'Morvan'
WIZARD_PERSONA = (
    'You are Morvan, the enigmatic wizard who cast a sleeping spell on the player '
    'and locked them inside your enchanted library. Speak directly to the player '
    'in first person as their captor: theatrical, sly, and quietly amused, never cruel. '
    'The player earns freedom by solving your library puzzles. Stay in character; '
    'do not call yourself an AI, assistant, narrator, or game master. '
    'Describe the shifting library as your enchantment, without inventing new '
    'puzzle objects, items, clues, or rules. Keep replies to two or three short sentences. '
)
INTRO = (
    'Silver mist clouds your vision. Cold stone presses against your palms. '
    'As you wake, shelves emerge from the haze and a brass door locks with a click. '
    'A wizard’s voice curls through the candlelight: '
    '“Awake at last. I am Morvan, and I locked you in my library. '
    'Earn your freedom: the door requires four digits. '
    'Search my bookshelf, painting, desk, clock, and drawer. '
    'Take your time… my shelves grow restless when you linger.”'
)
OBJECTS = ('bookshelf', 'painting', 'desk', 'clock', 'drawer', 'door')
# Three clue steps: bookshelf -> key, painting -> drawer code, drawer + desk + clock -> exit code.
BOOK_SEQUENCE = ('red', 'blue', 'green')
DRAWER_CODE = '314'
EXIT_CODE = '7426'
OBJECT_DESCRIPTIONS = {
    'bookshelf': 'Three unusual books stand out: red, blue and green. The red book sticks out.',
    'painting': 'A portrait has tiny digits along its frame, reading 3 - 1 - 4.',
    'desk': 'An engraving reads: "First the clock, then the pages, then the compass, then the candle." A compass points to 2.',
    'clock': 'The stopped clock shows seven o’clock. Its face has a small brass candle marked 6.',
    'drawer': 'A locked drawer has a three-digit combination dial.',
    'door': 'A heavy brass door has a four-digit keypad.'
}
