import sqlite3
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup


def get_soup(url_to_parse):
    response = requests.get(url_to_parse)
    html_text = response.text
    return BeautifulSoup(html_text, "html.parser")


def get_sum_of_team_stat(links_to_player_of_team):
    return sum([float(get_player_stat(link_to_player)) for link_to_player in links_to_player_of_team])


def get_player_stat(url_to_player):
    soup = get_soup(url_to_parse=url_to_player)
    return soup.find("span", {"class": "statsVal"}).text


def get_rank(rank):
    if rank <= 10:
        return 1
    elif 10 < rank <= 20:
        return 0.9
    elif 20 < rank <= 30:
        return 0.7
    elif 30 < rank <= 100:
        return 0.55
    elif 100 < rank:
        return 0.4
    elif rank == 1000:
        return 0.2


def get_score(**kwargs):
    return ((kwargs['stat'] * 9 / 7.5) + (kwargs['stat_of_map'] * 7 / 300) + (kwargs['count_of_won'] * 4)) * kwargs[
        'world_rating']


def get_score_in_percent(score):
    if score >= 1.7:
        return 'В проходе уверен на 90%'
    if score < 1.7:
        return 'Возможны трудности с проходом'


class GameAnalyser:
    def __init__(self, url_to_math):
        self.url_to_math = url_to_math
        self.tz = pytz.timezone('Europe/Kiev')
        self.game_soup = get_soup(url_to_parse=url_to_math)

    def get_teams_stats_of_map(self, i):
        stats_of_maps = self.get_stats_of_map()
        return sum([int(stats_of_maps[j][:-1]) if stats_of_maps[j] != '-' else 35 for j in range(i, 6, 2)])

    def get_stats_of_map(self):
        stats_of_map = [div.find('a').text for div in self.game_soup.findAll(class_='map-stats-infobox-winpercentage')]
        return stats_of_map

    def get_count_of_won(self, i):
        matches = self.game_soup.findAll(class_='table matches')
        return float(len(matches[i].findAll(class_='spoiler result won')) / 5)

    def get_world_rating(self, i):
        link_to_first_team = "https://www.hltv.org" + self.game_soup.find(class_="team%s-gradient" % (i + 1)).find('a')[
            'href']
        soup = get_soup(link_to_first_team)
        return get_rank(int(soup.find(class_="value").text[1:])) or 1000

    def get_kof(self, i):
        res = self.game_soup.find(class_='onexbet-odds geoprovider_1xbet betting_provider')
        team_kofs = []
        if len(res.findAll('a')) == 0:
            return 'Не известно'
        for link in res.findAll('a'):
            if link.text not in ['-', '']:
                team_kofs.append(link.text or "??")
        return team_kofs[i]

    def get_team_info(self):
        info = dict(main_info={}, teams=[{}, {}])
        start_time = self.game_soup.find(class_='time').text
        info['main_info']['start_time'] = start_time
        start_date = int(self.game_soup.find(class_='time')['data-unix'][:-3])
        info['main_info']['start_date'] = datetime.fromtimestamp(start_date).astimezone(self.tz)
        div_with_team = self.game_soup.findAll(class_='box-headline flex-align-center')
        players_links = self.game_soup.find_all(class_="player")
        players = []
        for player_link in players_links:
            if player_link.find('a')['href'] not in players:
                players.append(player_link.find('a')['href'])
        all_links_to_players = ["https://www.hltv.org" + link for link in players]
        count_of_player_in_team = int(len(all_links_to_players) / 2)
        all_links_to_players = [all_links_to_players[:count_of_player_in_team],
                                all_links_to_players[count_of_player_in_team:]]
        for i, dev_with_name in enumerate(div_with_team):
            info['teams'][i]['name'] = (dev_with_name.find('img')['alt'])
        for i, team_players in enumerate(all_links_to_players):
            info['teams'][i]['links'] = team_players
            info['teams'][i]['stat'] = get_sum_of_team_stat(team_players)
            info['teams'][i]['stat_of_map'] = self.get_teams_stats_of_map(i=i)
            info['teams'][i]['count_of_won'] = self.get_count_of_won(i=i)
            info['teams'][i]['world_rating'] = self.get_world_rating(i=i)
            info['teams'][i]['score'] = get_score(**info['teams'][i])
            info['teams'][i]['kof'] = self.get_kof(i=i)

        return info

    def game_analyser(self):
        link_to_game = self.url_to_math
        game_info = self.get_team_info()
        first_team = game_info['teams'][0]['name']
        first_team_kof = game_info['teams'][0]['kof']
        second_team_kof = game_info['teams'][1]['kof']
        second_team = game_info['teams'][1]['name']
        start_time = game_info['main_info']['start_time']
        if game_info['teams'][1]['score'] > game_info['teams'][0]['score']:
            score = game_info['teams'][1]['score'] - game_info['teams'][0]['score']
            result_of_game = 1

        else:
            score = float(game_info['teams'][0]['score']) - float(game_info['teams'][1]['score'])
            result_of_game = 0
        score_in_percent = get_score_in_percent(score=score)
        return dict(
            first_team=first_team,
            second_team=second_team,
            link_to_game=link_to_game,
            start_time=start_time,
            score_in_percent=score_in_percent,
            winner=game_info['teams'][result_of_game]['name'],
            first_team_kof=first_team_kof,
            second_team_kof=second_team_kof,
        )


class GamesParser:
    def __init__(self):
        self.url = "https://www.hltv.org/matches"
        self.tz = pytz.timezone('Europe/Kiev')
        self.db = DataBase()

    def get_days_games(self):
        page_html = requests.get(self.url).text
        soup = BeautifulSoup(page_html, "html.parser")
        divs_matches = [match for match in soup.findAll(class_="a-reset block upcoming-match standard-box")]
        matches = []
        for match in divs_matches:
            teams = match.findAll(class_="team")
            if len(teams) == 2:
                date_time = int(match['data-zonedgrouping-entry-unix'][:-3])
                match_date_time = datetime.fromtimestamp(date_time).astimezone(self.tz)
                matches.append(dict(
                    first_team=teams[0].text,
                    second_team=teams[1].text,
                    link='https://www.hltv.org' + match['href'],
                    datetime=match_date_time,
                ))
        self.db.update_games(matches)

        return matches


class ChanelAdmin:
    def __init__(self):
        self.parser = GamesParser()

    def send_game(self, link_to_match):
        game_analyser = GameAnalyser(url_to_math=link_to_match)
        game_info = game_analyser.game_analyser()
        text = "WINNER: {winner}\n{first_team} 🆚 {second_team} ➡\n️Время начала: {start_time}" \
               "\nКоеф п1: {first_team_kof}\nКоеф п2: {second_team_kof}\nСсылка на игру: {link_to_game}" \
               "\n {score_in_percent}".format(
            **game_info)
        return text


class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect("database.db")
        self.cursor = self.conn.cursor()

    def create_database(self):
        self.cursor.execute("""CREATE TABLE games
                      (first_team text, second_team text, link text, datetime datetime, UNIQUE(link))
                   """)

    def update_games(self, matches):
        games = [(
            match.get('first_team'),
            match.get('second_team'),
            match.get('link'),
            match.get('datetime')
        ) for match in matches]

        self.cursor.executemany("INSERT OR IGNORE INTO games VALUES (?,?,?,?)", games)
        self.conn.commit()

    def get_games(self):
        self.cursor.execute("SELECT * FROM games")
        rows = self.cursor.fetchall()
        return rows
