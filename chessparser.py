import pyautogui
import time
from dataclasses import dataclass
from enum import Enum
import datetime as dt
import win32clipboard
import multiprocessing

png_dir = 'D:/Projects/chess.com/analyze every game/Bot/button png/'


def click_button(filename, sleep_seconds=0.01, x=0, y=0, width=1920, height=1080):
    button = pyautogui.locateOnScreen(
        png_dir+filename, confidence=0.95, region=(x, y, width, height))
    if button is None:
        return
    button = pyautogui.center(button)
    pyautogui.click(button)
    time.sleep(sleep_seconds)


def is_on_screen(filename, confidence=0.99, x=0, y=0, width=1920, height=1080):
    button = pyautogui.locateOnScreen(
        png_dir+filename, confidence, region=(x, y, width, height))
    if button is None:
        return False
    return True


def _is_on_screen(filename, process, return_dict, run, confidence=0.99, x=0, y=0, width=1920, height=1080):
    button = pyautogui.locateOnScreen(
        png_dir+filename, confidence, region=(x, y, width, height))
    if button is not None:
        return_dict[process] = filename
        run.clear()


def is_on_screen_multiprocessed(filenames, confidence=0.99, x=0, y=0, width=1920, height=1080):
    processes = []
    manager = multiprocessing.Manager()
    return_values = manager.dict()
    run = manager.Event()
    run.set()
    for i, filename in enumerate(filenames):
        process = multiprocessing.Process(
            target=_is_on_screen, args=(filename, i, return_values, run, confidence, x, y, width, height))
        processes.append(process)
        process.start()

    while run.is_set():
        pass
    for process in processes:
        process.terminate()

    return list(return_values.values())[0]


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


mark_pngs = {'best.png': Mark.BEST,
             'excellent.png': Mark.EXCELLENT,
             'good.png': Mark.GOOD,
             'inaccuracy.png': Mark.INACCURACY,
             'mistake.png': Mark.MISTAKE,
             'theory.png': Mark.THEORY,
             'blunder.png': Mark.BLUNDER,
             'miss.png': Mark.MISS,
             'great.png': Mark.GREAT,
             'forced.png': Mark.FORCED,
             'brilliant.png': Mark.BRILLIANT}


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
    accuracy = tuple[float, float]
    time_control: tuple[int, int]
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
    time_control = pgn[0:end].split("+")
    if len(time_control) - 1:
        time_control = (int(time_control[0]), int(time_control[1]))
    else:
        time_control = (int(time_control[0]), 0)
    pgn_dict["Time control"] = time_control

    start = pgn.find("Termination")
    pgn = pgn[start+13:]
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
    pgnsplit = pgn.replace("\n", ' ')
    pgnsplit = pgnsplit.split()
    moves = []
    times = []
    for i, entry in enumerate(pgnsplit):
        if entry == "{[%clk":
            moves.append(pgnsplit[i-1])
            times.append(pgnsplit[i+1][0:-2])

    pgn_dict['Moves'] = moves
    pgn_dict['Timestamps'] = time_to_seconds(times)

    return pgn_dict


def time_to_seconds(time_list):
    result = []
    for i in time_list:
        time = i.split(":")
        time = [float(x) for x in time]
        result.append(time[0]*3600+time[1]*60+time[2])
    return result


def parse_review():
    # Get PGN
    click_button('share.png')
    click_button('anotation.png')
    click_button('timestamps.png')
    click_button('comments_true.png')
    click_button('keymoments_true.png')
    # click pgn field
    pyautogui.click(x=1171, y=570)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    pgn = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    # click the x
    pyautogui.click(x=1233, y=280)
    pgn_dict = pgn_to_dict(pgn)
    marks = []
    # click next move button
    pyautogui.click(x=1329, y=1000)
    for move in pgn_dict["Moves"]:
        mark = is_on_screen_multiprocessed(
            mark_pngs, confidence=0.6, x=1215, y=130, width=500, height=830)
        marks.append(mark)
        pyautogui.click()

    moves = []
    for i, move in enumerate(pgn_dict["Moves"]):
        notation = move
        is_check = move[-1] == '+'
        is_mate = move[-1] == '#'
        mark = mark_pngs[marks[i]]
        seconds_left = pgn_dict['Timestamps'][i]
        if i == 0:
            seconds_spent = pgn_dict['Time control'][0] - \
                seconds_left + pgn_dict['Time control'][1]
        else:
            seconds_spent = pgn_dict['Timestamps'][i-2] - \
                seconds_left + pgn_dict['Time control'][1]
        moves.append(Move(notation,
                          seconds_spent,
                          seconds_left,
                          mark,
                          is_check,
                          is_mate))

    white_rating = pyautogui.locateCenterOnScreen(
        png_dir+'white_rating.png', 0.6, region=(1215, 130, 500, 830))
    pyautogui.moveTo(white_rating)
    pyautogui.moveRel(0, -10)
    pyautogui.doubleClick()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    white_rating = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    white_rating = pyautogui.locateCenterOnScreen(
        png_dir+'black_rating.png', 0.6, region=(1215, 130, 500, 830))
    pyautogui.moveTo(white_rating)
    pyautogui.moveRel(0, -10)
    pyautogui.doubleClick()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    black_rating = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    return pgn, pgn_dict, marks


if __name__ == "__main__":
    time.sleep(5)
    pgn, pgn_dict, marks = parse_review()
