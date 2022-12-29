import pyautogui
import time
from dataclasses import dataclass
from enum import Enum
import datetime as dt
import win32clipboard
import threading
import datetime
import pickle

png_dir = 'D:/Projects/chess.com/analyze every game/button png/'
game_dir = 'D:/Projects/chess.com/analyze every game/saved games/'


def click_button(filename, sleep_seconds=0.01, x=0, y=0, width=1920, height=1080):
    button = None
    n = 0
    while button is None:
        button = pyautogui.locateOnScreen(
            png_dir+filename, confidence=0.95, region=(x, y, width, height))
        n += 1
        if n == 4:
            break

    if button is None:
        return False
    button = pyautogui.center(button)
    pyautogui.click(button)
    time.sleep(sleep_seconds)
    return True


def is_on_screen(filename, confidence=0.99, x=0, y=0, width=1920, height=1080):
    button = pyautogui.locateOnScreen(
        png_dir+filename, confidence, region=(x, y, width, height))
    if button is None:
        return False
    return True


def _is_on_screen(filename, return_list, confidence=0.99, x=0, y=0, width=1920, height=1080):
    button = pyautogui.locateOnScreen(
        png_dir+filename, confidence, region=(x, y, width, height))
    if button is not None:
        return_list.append(filename)


def is_on_screen_multiprocessed(filenames, confidence=0.99, x=0, y=0, width=1920, height=1080):
    return_value = []
    for i, filename in enumerate(filenames):
        thread = threading.Thread(
            target=_is_on_screen, args=(filename, return_value, confidence, x, y, width, height), daemon=True)
        thread.start()

    while not return_value:
        pass

    return return_value[0]


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
    pass


class DrawReason(Reason):
    STALEMATE = 0
    REPETITION = 1
    AGREEMENT = 2
    INSUFFICIENT_MATERIAL = 3
    FIFTY_MOVE_RULE = 4
    TIMEOUT = 5


class VictoryReason(Reason):
    CHECKMATE = 1
    RESIGNATION = 2
    ABANDONEMENT = 3
    TIMEOUT = 4


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
    names: tuple[str, str]
    elos: tuple[int, int]
    accuracy: tuple[float, float]
    time_control: tuple[int, int]
    start_datetime: dt.datetime
    end_datetime: dt.datetime
    url: str
    moves: list[Move]
    result: tuple[Winner, Reason]
    skill_level: tuple[int, int]
    ECO: str
    PGN: str

    def save(self):
        filename = self.start_datetime.strftime('%Y-%m-%d %Hh%Mm%Ss')
        with open(game_dir+filename, 'wb') as file:
            pickle.dump(self, file)
            print(
                f'Game between {self.names[0]}({self.elos[1]}) and {self.names[1]}({self.elos[1]}) saved with filename "{filename}"')


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
    click_button('share.png')
    click_button('anotation.png')
    click_button('timestamps.png')
    click_button('comments_true.png')
    click_button('keymoments_true.png')
    pyautogui.moveTo(x=1172, y=551)
    pyautogui.moveRel(0, 30)
    pyautogui.click()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    pgn = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    click_button('exitpgn.png')
    pgn_dict = pgn_to_dict(pgn)

    white_accuracy = pyautogui.locateCenterOnScreen(
        png_dir+'white_accuracy.png', confidence=0.9, region=(1215, 130, 500, 830))
    pyautogui.moveTo(white_accuracy)
    pyautogui.moveRel(0, -10)
    pyautogui.doubleClick()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    white_accuracy = float(win32clipboard.GetClipboardData())
    win32clipboard.CloseClipboard()

    black_accuracy = pyautogui.locateCenterOnScreen(
        png_dir+'black_accuracy.png', confidence=0.9, region=(1215, 130, 500, 830))
    pyautogui.moveTo(black_accuracy)
    pyautogui.moveRel(0, -10)
    pyautogui.doubleClick()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    black_accuracy = float(win32clipboard.GetClipboardData())
    win32clipboard.CloseClipboard()

    accuracy = (white_accuracy, black_accuracy)

    marks = []
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
        png_dir+'white_rating.png', confidence=0.9, region=(1215, 130, 500, 830))
    pyautogui.moveTo(white_rating)
    pyautogui.moveRel(0, -10)
    pyautogui.doubleClick()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    white_rating = int(win32clipboard.GetClipboardData())
    win32clipboard.CloseClipboard()

    black_rating = pyautogui.locateCenterOnScreen(
        png_dir+'black_rating.png', confidence=0.9, region=(1215, 130, 500, 830))
    pyautogui.moveTo(black_rating)
    pyautogui.moveRel(0, -10)
    pyautogui.doubleClick()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.01)
    win32clipboard.OpenClipboard()
    black_rating = int(win32clipboard.GetClipboardData())
    win32clipboard.CloseClipboard()

    skill_level = (white_rating, black_rating)
    names = (pgn_dict["White"], pgn_dict["Black"])
    elos = (pgn_dict["White Elo"], pgn_dict["Black Elo"])
    time_control = pgn_dict["Time control"]
    ECO = pgn_dict["ECO"]
    url = pgn_dict["Link"]
    if pgn_dict["Termination"].find(names[0]) != -1:
        winner = Winner.WHITE
    elif pgn_dict["Termination"].find(names[1]) != -1:
        winner = Winner.BLACK
    else:
        winner = Winner.DRAW
    if winner.name != 'DRAW':
        if pgn_dict["Termination"].find('time') != -1:
            reason = VictoryReason.TIMEOUT
        elif pgn_dict["Termination"].find('checkmate') != -1:
            reason = VictoryReason.CHECKMATE
        elif pgn_dict["Termination"].find('resignation') != -1:
            reason = VictoryReason.RESIGNATION
        else:
            reason = VictoryReason.ABANDONEMENT
    else:
        if pgn_dict["Termination"].find('agreement') != -1:
            reason = DrawReason.AGREEMENT
        elif pgn_dict["Termination"].find('repetition') != -1:
            reason = DrawReason.REPETITION
        elif pgn_dict["Termination"].find('stalemate') != -1:
            reason = DrawReason.STALEMATE
        elif pgn_dict["Termination"].find('timeout') != -1:
            reason = DrawReason.TIMEOUT
        elif pgn_dict["Termination"].find('insufficient material') != -1:
            reason = DrawReason.INSUFFICIENT_MATERIAL
        else:
            reason = DrawReason.FIFTY_MOVE_RULE
    result = (winner, reason)
    start_datetime = datetime.datetime.strptime(pgn_dict['Start date']+" "+pgn_dict['Start time'],
                                                '%Y.%m.%d %H:%M:%S')
    end_datetime = datetime.datetime.strptime(pgn_dict['End date']+" "+pgn_dict['End time'],
                                              '%Y.%m.%d %H:%M:%S')
    game = Game(names,
                elos,
                accuracy,
                time_control,
                start_datetime,
                end_datetime,
                url,
                moves,
                result,
                skill_level,
                ECO,
                pgn)

    return game


def parse_archive_page():
    pyautogui.scroll(-250)
    x = 945
    y_list = [115+i*75 for i in range(13)]
    analysis_fail = []
    for y in y_list:
        pyautogui.click(x, y)
        time.sleep(0.01)
        while not is_on_screen('analysis_loaded.png', confidence=0.6):
            analysis_fail.append(click_button('analysis.png'))
        game = parse_review()
        game.save()
        pyautogui.click(20, 55)
        pyautogui.moveTo(x, y)
        while not is_on_screen('refreshicon.png', confidence=0.9):
            if True in analysis_fail:
                pyautogui.click(20, 55)
                pyautogui.moveTo(x, y)
            analysis_fail = []
    pyautogui.scroll(-1175)
    for y in y_list:
        pyautogui.click(x, y)
        time.sleep(0.01)
        while not is_on_screen('analysis_loaded.png', confidence=0.6):
            click_button('analysis.png')
        game = parse_review()
        game.save()
        pyautogui.click(20, 55)
        pyautogui.moveTo(x, y)
        while not is_on_screen('refreshicon.png', confidence=0.9):
            if True in analysis_fail:
                pyautogui.click(20, 55)
                pyautogui.moveTo(x, y)
            analysis_fail = []
    pyautogui.scroll(-1175)
    for y in y_list:
        pyautogui.click(x, y)
        time.sleep(0.01)
        while not is_on_screen('analysis_loaded.png', confidence=0.6):
            click_button('analysis.png')
        game = parse_review()
        game.save()
        pyautogui.click(20, 55)
        pyautogui.moveTo(x, y)
        while not is_on_screen('refreshicon.png', confidence=0.9):
            if True in analysis_fail:
                pyautogui.click(20, 55)
                pyautogui.moveTo(x, y)
            analysis_fail = []
    pyautogui.scroll(-1175)
    for y in y_list[0:11]:
        pyautogui.click(x, y)
        time.sleep(0.01)
        while not is_on_screen('analysis_loaded.png', confidence=0.6):
            click_button('analysis.png')
        game = parse_review()
        game.save()
        pyautogui.click(20, 55)
        while not is_on_screen('refreshicon.png', confidence=0.9):
            if True in analysis_fail:
                pyautogui.click(20, 55)
                pyautogui.moveTo(x, y)
            analysis_fail = []


def parse_n_pages(n):
    for i in range(n):
        parse_archive_page()
        time.sleep(0.1)
        print(f'Parsed page {i+1}')
        click_button('arrow.png')
        while not is_on_screen('refreshicon.png', confidence=0.9):
            pass


if __name__ == "__main__":
    time.sleep(5)
    parse_n_pages(10)
    # game = parse_review()
    pass
