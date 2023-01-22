import analysisscraper as scraper
import json

class SettingsNotSet(Exception):
    pass

if __name__ == "__main__":
    # Set these variables
    # You have to have chess.com membership for tis to work
    username = ''
    cookie = {'PHPSESSID': '',
              'CHESSCOM_REMEMBERME': ''}
    
    
    if not (username and cookie['PHPSESSID'] and cookie['PHPSESSID']):
        raise SettingsNotSet('Set the username and cookies')
    
    # Set n to however many of your last games you want to analyze
    # Analyzing 1 game takes a minimum of 10 seconds(however, if the analysis exists on
    # chess.com servers then it takes 2-3 seconds max)
    n = 50
    games = scraper.get_all_games(username, start_year=2022)
    analyzed_games = scraper.get_analysis_for_multiple(
        games[-n:], cookie, 'analyzed games.json')
    brilliant_moves = []
    for game in analyzed_games:
        if not game['analysis']:
            brilliant_moves.append(0)
            continue
        color = (game["black"]["username"] == username)*'black' + \
            (game["white"]["username"] == username)*'white'
        tally = game['analysis']['tallies'][color]
        brilliant_moves.append(tally['brilliant'])
    print(
        f"You played a grand total of {sum(brilliant_moves)} brilliant move(s) in your last {n} games.")
    for i, j in enumerate(brilliant_moves):
        if not j:
            continue
        print(f"You played {j} brilliant move(s) in this game:")
        print(analyzed_games[i]['url'])
        color = (analyzed_games[i]["black"]["username"] == username)*'black' + \
            (analyzed_games[i]["white"]["username"] == username)*'white'
        for i, position in enumerate(analyzed_games[i]['analysis']['positions'][1:]):
            if position['classificationName'] == 'brilliant' and position['color'] == color:
                print(f"Move {i//2+1} by {color} was brilliant!")
