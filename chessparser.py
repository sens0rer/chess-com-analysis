import pyautogui
import time
from dataclasses import dataclass
from enum import Enum
import datetime as dt
import win32clipboard


def click_button(filename):
    button = pyautogui.locateOnScreen(filename, confidence=0.7)
    if button is None:
        return
    button = pyautogui.center(button)
    # TODO: might not work, change to x and y ?
    pyautogui.click(button)


def refresh_page():
    pyautogui.press('F5')
    all_done = pyautogui.locateOnScreen(
        'refreshicon.png', confidence=0.7)
    if all_done is not None:
        return
    refresh_page()


class Mark(Enum):
    FORCED = 0
    THEORY = 1
    BRILLIANT = 2
    GREAT = 3
    BEST = 4
    EXCELLENT = 5
    GOOD = 6
    INACCURACY = 7
    MISTAKE = 8
    BLUNDER = 9
    MISS = 10


class Winner(Enum):
    DRAW = 0
    WHITE = 1
    BLACK = 2


class Reason(Enum):
    CHECKMATE = 0
    STALEMATE = 1
    REPETITION = 2
    TIME = 3
    AGREEMENT = 4


@dataclass
class Move:
    notation: str
    seconds_spent: float
    seconds_left: float
    mark: Mark
    is_check: bool
    is_mate: bool


@dataclass
class Game:
    names = tuple[str, str]
    elos = tuple[int, int]
    time_control: str
    start_datetime: dt.datetime
    end_datetime: dt.datetime
    url: str
    moves: list[Move]
    result: tuple[Winner, Reason]
    skill_level: tuple[int, int]
    ECO: str
    PGN: str


def pgn_to_dict(pgn):
    pass


def parse_review():
    # Get PGN
    click_button('share.png')
    click_button('annotation.png')
    click_button('timestamps.png')
    click_button('comments_true.png')
    click_button('keymoments_true.png')
    pgn_coordinates = pyautogui.locateOnScreen('timestamps_true.png',
                                               confidence=0.7)
    pgn_coordinates = pyautogui.center(pgn_coordinates)
    pyautogui.click(x=pgn_coordinates[0], y=pgn_coordinates[1]+20)
    pyautogui.hotkey('ctrl', 'c')
    win32clipboard.OpenClipboard()
    pgn = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    click_button('exitpgn.png')
    moves = []
    skill_level = 0, 0
    while next_button := pyautogui.locateOnScreen('nextmove.png',
                                                  confidence=0.7) is not None:
        pass


if __name__ == "__main__":
    pass
