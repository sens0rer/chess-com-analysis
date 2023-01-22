import requests
import json
import asyncio
import websockets
from websockets import InvalidStatusCode
import time
from os.path import exists as file_exists


class AuthorizationError(Exception):
    "For handling errors related to restricted access to chess.com API"
    pass

class RetrievalError(Exception):
    "For handling errors related to retrieving specific games from chess.com API"
    pass


def update_cookies(cookies: dict):
    """
    This function updates 'PHPSESSID' in the cookies dictionary if this cookie is outdated.
    Requires 'CHESSCOM_REMEMBERME' to be set.

    Parameters:
        cookies (dict): Cookie dictionary that will be updated.
    """
    if cookies.get('CHESSCOM_REMEMBERME') is None:
        return
    url = 'https://www.chess.com/home'
    request = requests.get(url, cookies=cookies)
    cookies['PHPSESSID'] = request.cookies.get(
        'PHPSESSID', cookies.get('PHPSESSID', ''))


def get_game(url: str) -> dict:
    """
    Returns a specific game from chess.com public API.

    Parameters:
        url (str): Link to the game. Example: 'https://www.chess.com/game/live/67952727689'
    Returns:
        dict: Dictionary containing the game data.
    """
    game_type = url.removeprefix('https://www.chess.com/game/')
    game_type, game_id = game_type.split('/')
    request_url = f'https://www.chess.com/callback/{game_type}/game/{game_id}'
    request = requests.get(request_url)
    date = request.json().get('game',{}).get('pgnHeaders',{}).get("Date",'..')
    year, month, = date.split('.')
    username = request.json().get('game',{}).get('pgnHeaders',{}).get("White",'')
    if not (year and month and username):
        error_text = f'Something went wrong while getting the game from {url}\n'
        error_text += 'Information for debugging:\n'
        error_text += f'Request status code:{request.status_code}\n'
        error_text += f'Request contents: \n {request.content}'
        raise RetrievalError(error_text)
    request_url = f'https://api.chess.com/pub/player/{username}/games/{year}/{month}'
    request = requests.get(url)
    for game in request.json()['games']:
        if url == game['url']:
            return game


def get_all_games(username: str,
                  start_year: int = 2019,
                  start_month: int = 1,
                  filename: str = None) -> list[dict]:
    """
    Returns a list of games from chess.com public API.

    Parameters:
        username (str): Username of the player whose games you want to get.
        start_year (int): The starting year. Defaults to 2019.
        start_month (int): Number of the starting month. Defaults to 1 (January).
        filename (str): If specified, the results will be saved to this file in json format.
    Returns:
        list[dict]: List of dictionaries representing games played from the specified date.
    """
    games = []
    year = start_year
    month = start_month
    while True:
        # 1-month//10 checks if the month has 1 or 2 digits
        # '0'*(1-month//10) adds a zero at the start if the month has 1 digit
        str_month = '0'*(1-month//10)+str(month)
        url = f'https://api.chess.com/pub/player/{username}/games/{year}/{str_month}'
        request = requests.get(url)
        if request.status_code != 200:
            break
        print(f'Fetched {len(games)} games up to {str_month}/{year}', end='\r')
        games.extend(request.json()['games'])
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
    print(f'Fetched {len(games)} games up to {str_month}/{year}')

    if filename is None:
        return games

    with open(filename, 'w') as file:
        json.dump(games, file)
        print(f"Saved {len(games)} games to {filename}")
    return games


def _build_msg(game: dict,
               cookies: dict,
               language: str = "en_US",
               depth: int = 18,
               engine: str = "stockfish12") -> dict:
    """
    Builds the message to be sent to the websocket
    (wss://analysis-va.chess.com/)

    Parameters:
        game (dict): Game dictionary received from get_all_games() or get_game().
        cookies (dict): A dictionary of cookies that authenticate the user.
        language (str): Language of analysis. Defaults to 'en_US'.
        depth (int): Depth of analysis. Defaults to 18.
        engine(int): Engine type. Defaults to 'stockfish12'
    Returns:
        dict: Message to be sent to the websocket.
    """
    message = {"action": "gameAnalysis",
               "game": {"pgn": ""},
               "options": {"caps2": True,
                           "depth": 18,
                           "getNullMove": True,
                           "engineType": "stockfish12",
                           "source": {"gameId": "",
                                      "gameType": "",
                                      "url": "",
                                      "token": "",
                                      "client": "web",
                                      "userTimeZone": ""},
                           "tep": {"ceeDebug": False,
                                   "lang": "en_US",
                                   "speechv2": True,
                                   "userColor": "white",
                                   "classificationv3": True}}}
    game_type = game['url'].removeprefix('https://www.chess.com/game/')
    game_type, game_id = game_type.split('/')
    pgn = game['pgn']
    message['game']['pgn'] = pgn
    message['options']['source']['gameId'] = game_id
    message['options']['source']['gameType'] = game_type
    message['options']['depth'] = depth
    message['options']['engineType'] = engine
    message['options']['tep']['lang'] = language

    # Get token
    url = f'https://www.chess.com/callback/auth/service/analysis?game_id={game_id}&game_type={game_type}'
    request = requests.get(url, cookies=cookies)
    if request.status_code != 200 and "not authorized" in request.json().get('message', ''):
        raise AuthorizationError(
            f'Cookie is outdated or invalid\nServer response: {request.status_code}\n{request.content}')
    message['options']['source']['token'] = request.json()['token']

    return message


async def _request_analysis(message: dict) -> dict:
    """
    Requests creating analysis from chess.com though the webscoket.
    (wss://analysis-va.chess.com/)

    Parameters:
        message (dict): Intial message to the websocket received from _build_msg().

    Returns:
        dict: Analysis of the game.

    """
    async with websockets.connect('wss://analysis-va.chess.com/') as websocket:
        await websocket.send(json.dumps(message))
        while True:
            message = await websocket.recv()
            msg_dict = json.loads(message)
            if msg_dict.get('action') == "progress":
                percentage = round(msg_dict.get("progress", 0.)*100)
                print(f"Creating analysis: {percentage}%", end="\r")
            if message == '{"action":"done"}':
                print("Creating analysis: 100%")
                return json.loads(last_message).get("data")
            if message == '{"err":1,"message":"game analysis request error - missing moves"}':
                return {}
            last_message = message


def get_analysis(game: dict,
                 cookies: dict,
                 language: str = "en_US",
                 depth: int = 18,
                 engine: str = "stockfish12",
                 generate_new: bool = False) -> dict:
    """
    Returns the analysis of a game.

    Parameters:
        game (dict): Game dictionary received from get_all_games() or get_games().
        cookies (dict): A dictionary of cookies that authenticate the user.
        language (str): Language of analysis. Defaults to 'en_US'.
        depth (int): Depth of analysis. Defaults to 18.
        engine(int): Engine type. Defaults to 'stockfish12'.
        generate_new (bool): If set to true requests that chess.com creates a new analysis even if there is an existing one. Might result in slower performance, but ensures that additional criteria like engine type, depth of analysis and language are met.
    Returns:
        dict: Dictionary with analysis data for the game.
    """
    # Failsafe for cases when user-set cookies are outdated
    update_cookies(cookies)
    game_type = game['url'].removeprefix('https://www.chess.com/game/')
    game_type, game_id = game_type.split('/')
    url = f'https://www.chess.com/callback/analysis/game/{game_type}/{game_id}/all'
    if not generate_new:
        request = requests.get(url, cookies=cookies)
        if request.status_code == 502:
            print("The server returned 502 Bad Gateway. Retrying in 20 seconds")
            time.sleep(20)
            request = requests.get(url, cookies=cookies)
        if request.status_code != 200 and "not authorized" in request.json().get('message', ''):
            raise AuthorizationError(
                f'Cookie is outdated or invalid\nServer response: {request.status_code}\n{request.content}')
        if request.json().get('data') is not None:
            print(f'Fetched analysis for game {game_type}/{game_id}')
            return request.json()["data"]["analysis"]
    message = _build_msg(game, cookies, language, depth, engine)
    analysis = asyncio.run(_request_analysis(message))
    time.sleep(10)
    print(f'Fetched analysis for game {game_type}/{game_id}')
    return analysis


def get_analysis_for_multiple(games: list[dict],
                              cookies: dict,
                              filename: str,
                              language: str = "en_US",
                              depth: int = 18,
                              engine: str = "stockfish12",
                              generate_new: bool = False,
                              ignore_exceptions: bool = False) -> list[dict]:
    """
    Analyzes every game in games and puts the result into a file in json format.
    (If the file continues previous analysis data, it will be preserved).

    Parameters:
        games (list[dict]): List of game dictionaries received from get_all_games() or get_game().
        cookies (dict): A dictionary of cookies that authenticate the user.
        filename (str): Savefile name.
        language (str): Language of analysis. Defaults to 'en_US'.
        depth (int): Depth of analysis. Defaults to 18.
        engine(int): Engine type. Defaults to 'stockfish12'.
        generate_new (bool): If set to True requests that chess.com creates a new analysis even if there is an existing one. Might result in slower performance, but ensures that additional criteria like engine type, depth of analysis and language are met.
        ignore_exceptions(bool): If set to True every exception will be caught and analysis will be restarted after a 120 second delay. Recommended to keep at False.
    Returns:
        list[dict]: A list of game dictionaries. Analysis can be accessed with the 'analysis' key.
    """
    while True:
        # Create a savefile if it doesn't exist
        if not file_exists(filename):
            with open(filename, 'w') as file:
                json.dump([], file)
        # Load previous data from the savefile
        with open(filename, 'r') as file:
            analyzed_games = json.load(file)
            # Remove games that were saved without analysis
            analyzed_games = [
                i for i in analyzed_games if i.get('analysis') is not None]
            analyzed_urls = [i.get('url') for i in analyzed_games]
        try:
            for game in games:
                if game['url'] in analyzed_urls:
                    continue
                print(f'Analyzing game {games.index(game)+1}/{len(games)}:')
                print(game['url'])
                if game['rules'] != 'chess':
                    print(
                        f"Skipping this game because it was played in a custom gamemode({game['rules']}) and cannot be analyzed")
                    continue
                analyzed_games.append(game)
                analyzed_games[-1]['analysis'] = get_analysis(
                    game, cookies, language, depth, engine, generate_new)
            break
        except AuthorizationError:
            # Save progress and propagate the exception
            with open(filename, 'w') as file:
                json.dump(analyzed_games, file)
            raise
        except InvalidStatusCode:
            # Save progress and restart after a delay
            print("Websocket rate limit hit. Retrying in 120 seconds")
            with open(filename, 'w') as file:
                json.dump(analyzed_games, file)
            time.sleep(120)
        except Exception as err:
            # Save progress and restart after a delay if ignore_exceptions is set to True
            with open(filename, 'w') as file:
                json.dump(analyzed_games, file)
            if not ignore_exceptions:
                print(f"{type(err).__name__} was raised: {err}")
                print("Retrying in 120 seconds")
                raise
            time.sleep(120)
    # Save the result
    with open(filename, 'w') as file:
        json.dump(analyzed_games, file)
    return analyzed_games
