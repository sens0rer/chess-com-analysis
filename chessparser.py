import pyautogui
import time
from dataclasses import dataclass
from enum import Enum
import datetime as dt
import win32clipboard

png_dir = 'D:/Projects/chess.com/analyze every game/Bot/button png/'


def click_button(filename):
    button = pyautogui.locateOnScreen(png_dir+filename, confidence=0.95)
    if button is None:
        return
    button = pyautogui.center(button)
    # TODO: might not work, change to x and y ?
    pyautogui.click(button)
    time.sleep(0.01)


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
    pgn_dict = {}

    start = pgn.find("White")
    pgn = pgn[start+7:]
    end = pgn.find('"]')
    pgn_dict["White"] = pgn[0:end]

    start = pgn.find("Black")
    pgn = pgn[start+7:]
    end = pgn.find('"]')
    pgn_dict["Black"] = pgn[0:end]

    start = pgn.find("Result")
    pgn = pgn[start+8:]
    end = pgn.find('"]')
    pgn_dict["Result"] = pgn[0:end]

    start = pgn.find("ECO")
    pgn = pgn[start+5:]
    end = pgn.find('"]')
    pgn_dict["ECO"] = pgn[0:end]

    start = pgn.find("UTCDate")
    pgn = pgn[start+9:]
    end = pgn.find('"]')
    pgn_dict["Start date"] = pgn[0:end]

    start = pgn.find("UTCTime")
    pgn = pgn[start+9:]
    end = pgn.find('"]')
    pgn_dict["Start time"] = pgn[0:end]

    start = pgn.find("WhiteElo")
    pgn = pgn[start+10:]
    end = pgn.find('"]')
    pgn_dict["White Elo"] = int(pgn[0:end])

    start = pgn.find("BlackElo")
    pgn = pgn[start+10:]
    end = pgn.find('"]')
    pgn_dict["Black Elo"] = int(pgn[0:end])

    start = pgn.find("TimeControl")
    pgn = pgn[start+13:]
    end = pgn.find('"]')
    pgn_dict["Time control"] = pgn[0:end]

    start = pgn.find("Termination")
    pgn = pgn[start+14:]
    end = pgn.find('"]')
    pgn_dict["Termination"] = pgn[0:end]

    start = pgn.find("EndDate")
    pgn = pgn[start+9:]
    end = pgn.find('"]')
    pgn_dict["End date"] = pgn[0:end]

    start = pgn.find("EndTime")
    pgn = pgn[start+9:]
    end = pgn.find('"]')
    pgn_dict["End time"] = pgn[0:end]

    start = pgn.find("Link")
    pgn = pgn[start+6:]
    end = pgn.find('"]')
    pgn_dict["Link"] = pgn[0:end]

    pgn = pgn[end+6:]
    pgn = pgn.split(" ")

    # pgn_dict['Moves'] =
    # pgn_dict['Timestamps'] =

    return pgn_dict


def parse_review():
    # Get PGN
    click_button('share.png')
    click_button('anotation.png')
    click_button('timestamps.png')
    click_button('comments_true.png')
    click_button('keymoments_true.png')
    pgn_coordinates = pyautogui.locateOnScreen(png_dir+'timestamps_true.png',
                                               confidence=0.7)
    pgn_coordinates = pyautogui.center(pgn_coordinates)
    pyautogui.click(x=pgn_coordinates[0], y=pgn_coordinates[1]+20)
    pyautogui.hotkey('ctrl', 'c')
    win32clipboard.OpenClipboard()
    pgn = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    click_button('exitpgn.png')
    moves = []
    while next_button := pyautogui.locateOnScreen(png_dir+'nextmove.png',
                                                  confidence=0.7) is not None:
        pass
    return pgn


if __name__ == "__main__":
    time.sleep(5)
    pgn = parse_review()
    pgn_dict = pgn_to_dict(pgn)
