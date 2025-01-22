import re
import requests
import pandas as pd
import datetime
import os
import time
import bs4 as bs # beautifulsoup

"""
This code scrapes NBA betting information from sportsbookreview.com

"""
START_DATE = datetime.datetime(2024, 10, 22)
END_DATE = datetime.datetime(2025, 1, 5)

SAMPLE_PAGE = "https://www.sportsbookreview.com/betting-odds/nba-basketball/"

##  best odds of winning the title at the beginning of the year.
TOP_TEAMS_FUTURES = ["Boston", "Oklahoma City", "Denver", "Minnesota", "New York"]

def money_vs_ats(start=START_DATE, end=END_DATE, dir='sbr'):
    data = clean_data(start=start, end=end, dir=dir)
    return money_vs_ats_from_data(data)

def money_vs_ats_from_data(data):
    combo_percents = get_money(data)
    ats_winners = data.winner_ats_name.value_counts()
    ats_losers = data.loser_ats_name.value_counts()

    df = pd.DataFrame({'winner': ats_winners, 'loser': ats_losers})
    df = df.fillna(0)
    df['ats_win_pct'] = df.winner / (df.winner + df.loser)
    df['money_percents'] = combo_percents

    return df

def get_ats_for_range(start=START_DATE, end=END_DATE, dir='sbr'):
    output = {}
    raw_dfs = {}
    range = pd.date_range(start, end).strftime("%Y-%m-%d")
    ### what I am trying to do here:
    ###  get the against-the-spread records for each day.
    for day in range:
        daily_data = clean_data(start=day, end=day, dir=dir)
        if daily_data is None:
            print(f"Skipping {day}, no data")
            continue
        raw_dfs[day] = daily_data
        # create a dataframe of everything in raw_dfs.values()
        season_to_date = pd.concat(raw_dfs.values())

        output[day] = money_vs_ats_from_data(season_to_date)

    return output


def get_money(df):
    ### get money percentages (combined home+away)
    home_percents = df.groupby('home_names').median('home_percents')['home_percents']
    away_percents = df.groupby('away_names').median('away_percents')['away_percents']
    combined_percents = home_percents.add(away_percents, fill_value=50)
    return combined_percents

def get_money_for_range(start=START_DATE, end=END_DATE, dir='sbr'):
    """
    this will do get_money for a range of dates. 
    
    each day uses all the data up to that day.

    For use with the 'superfade' 
    
    """
    raw_dfs = {}
    output = {}
    range = pd.date_range(start, end).strftime("%Y-%m-%d")
    for day in range:
        daily_data = clean_data(start=day, end=day, dir=dir)
        if daily_data is None:
            print(f"Skipping {day}, no data")
            continue
        
        raw_dfs[day] = daily_data
        # create a dataframe of everything in raw_dfs.values()
        season_to_date = pd.concat(raw_dfs.values())
        output[day] = get_money(season_to_date)

    return output

def handle_money_wl(df):
    ## name of the teams with the most/least money bet in this game.
    df['money_winner'] = None
    df['money_loser'] = None

    df.loc[(df.away_percents > 50), 'money_winner'] = df.loc[(df.away_percents > 50), 'away_names']
    df.loc[(df.away_percents > 50), 'money_loser' ] = df.loc[(df.away_percents > 50), 'home_names']

    df.loc[(df.away_percents < 50), 'money_winner'] = df.loc[(df.away_percents < 50), 'home_names']
    df.loc[(df.away_percents < 50), 'money_loser' ] = df.loc[(df.away_percents < 50), 'away_names']

    return df

def handle_lines(df):
 # extract the opening (away) lines
    open_away_lines = df.away_opens.str.extract(r'([\d\.\+\-]+)([\-\+][\d]+)')
    df['open_away_spread']  = open_away_lines[0].astype("float")
    df['open_away_vig']     = open_away_lines[1].astype("float")

    ## extract the closing away lines.
    lines = df.away_lines.str.extract(r'([\d\.\+\-]+)([\-\+][\d]+)')
    df['away_spread'] = lines[0].astype("float")
    df['away_vig'] = lines[1].astype("float")

    df['score_diff'] = df['away_scores'] - df['home_scores']

    # determine winner vs opening and closing line
    df['with_line'] = df['score_diff'] + df['away_spread']

    df['open_with_line'] = df['score_diff'] + df['open_away_spread']

    # if with_line < 0, then the away team lost, otherwise they won ATS
    df['winner_ats'] = None
    df['fave_dog'] = None

    df.loc[df.with_line > 0, 'winner_ats'] = 'AWAY'
    df.loc[df.with_line < 0, 'winner_ats'] = 'HOME'

    # if away_spread > 0 and with_line > 0: away underdog won
    #                        with_line < 0: away favorite won
    away_dogs  = ((df.away_spread > 0) & (df.with_line > 0))
    away_faves = ((df.away_spread > 0) & (df.with_line < 0))

    # if away_spread < 0 and with_line > 0: home favorite won
    #                                  < 0: home underdog won                             
    home_faves = ((df.away_spread < 0) & (df.with_line > 0))
    home_dogs  = ((df.away_spread < 0) & (df.with_line < 0))
    
    df.loc[away_dogs, 'fave_dog']  = "DOG"
    df.loc[away_faves, 'fave_dog'] = "FAVE"

    df.loc[home_faves, 'fave_dog'] = "FAVE"
    df.loc[home_dogs, 'fave_dog']  = "DOG"

    # add the name of the winner/loser against the spread.
    df['winner_ats_name'] = None
    df['loser_ats_name'] = None

    away_winners = df['winner_ats'] == 'AWAY'
    home_winners = df['winner_ats'] == 'HOME'
 
    df.loc[away_winners, 'winner_ats_name'] = df.loc[away_winners, 'away_names']
    df.loc[away_winners, 'loser_ats_name'] = df.loc[away_winners, 'home_names']

    df.loc[home_winners, 'winner_ats_name'] = df.loc[home_winners, 'home_names']
    df.loc[home_winners, 'loser_ats_name'] = df.loc[home_winners, 'away_names']

    return df

def clean_data(start=START_DATE, end=END_DATE, dir='sbr'):
    raw_data = merge_existing_data(start=start, end=end, dir=dir)

    if raw_data is not None:
        # throw out rows where this site doesn't have the scores.
        # there were some missing when I started this, but they're filled in now.
        missing_scores = sum((raw_data.home_scores == 0))
        if missing_scores > 0:
            print(f"missing scores from {missing_scores} games")
        df = raw_data[~(raw_data.home_scores == 0)].copy()
        df = handle_lines(df)
        df = handle_money_wl(df)
        return df
    return None

def merge_existing_data(start=START_DATE, end=END_DATE, dir='sbr'):
    range = pd.date_range(start, end).strftime("%Y-%m-%d")

    dfs = []
    for date in range:
        (year, month, day) = date.split("-")
        try:
            df_on = pd.read_csv(f"{dir}/{year}-{month}-{day}.csv")
            df_on['game_date'] = f"{year}-{month}-{day}"
            dfs.append(df_on)
        except:
            #print(f"failed on {date}")
            pass

    if len(dfs) > 0:   
        return pd.concat(dfs, ignore_index=True)
    else:
        return None

def fetch_data_range(start, end, dir='sbr'):
    range = pd.date_range(start, end).strftime("%Y-%m-%d")
    new_scrapes = []
    for date in range:
        print(f"On {date}")
        (year, month, day) = date.split("-")

        if not os.path.exists(f"{dir}/{year}-{month}-{day}.csv"):
            ### This is new data, or we are re-scraping.
            try:
                scraped = get_for_date(year, month, day, dir)
                new_scrapes.append(scraped)
                time.sleep(1.23)
            except Exception as e:
                print(f"choked on {date}")
                print(e)
        else:
            print(f"already got for {date}")
    return new_scrapes


def get_for_date(year, month, day, dir='sbr', save_csv=True):
    url = f"https://www.sportsbookreview.com/betting-odds/nba-basketball/?date={year}-{month}-{day}"
    req = requests.get(url)
    data = req.content
    scraped = scrape_a_page(data)
    if save_csv:
        out_name = f"{dir}/{year}-{month}-{day}.csv"
        scraped.to_csv(out_name)
    return scraped

def scrape_a_page(data):

    soup = bs.BeautifulSoup(data,'html.parser')
    table_soup = soup.find(id='tbody-nba')
    data_rows = table_soup.find_all(class_=re.compile("GameRows_containerTable"))
    participant_html = table_soup.find_all(class_=re.compile("GameRows_participantContainer"))

    away_names = []
    away_lines = []
    away_scores = []
    away_percents = []
    away_opens = []

    home_names = []
    home_lines = []
    home_scores = []
    home_percents = []
    home_opens = []

    away_done = None

    pd_response = pd.DataFrame()

    for p in participant_html:
        parti_box = p.find(class_=re.compile("GameRows_participantBox"))

        team_name = parti_box.get_text()

        score_box = p.find(class_=re.compile("GameRows_scores"))
        team_score = score_box.get_text()

        if away_done is None:
            away_done = team_name

            away_names.append(team_name)
            away_scores.append(team_score)
        else:
            home_names.append(team_name)
            home_scores.append(team_score)

            away_done = None

    for data_row in data_rows:
        away_line = None
        odds_cells = data_row.find_all(class_=re.compile("OddsCells_compact"))
        for cell in odds_cells:
            cell_text = cell.get_text()
            if away_line is None:
                away_lines.append(cell_text)
                away_line = cell_text
            else:
                home_lines.append(cell_text)
                away_line = None
                break # just taking the first one, BetMGM. there are other casinos.
    
    for data_row in data_rows:
        consensus_columns = data_row.find_all(class_=re.compile("GameRows_consensusColumn"))
        percent_container = consensus_columns[0]
        
        percent_cells = percent_container.find_all(class_="me-2")
        away_percent = None
        for cell in percent_cells:
            percent_text = cell.get_text()
            
            percent_int = int(percent_text[:-1])
            
            if away_percent is None:
                away_percents.append(percent_int)
                away_percent = percent_int
            else:
                home_percents.append(percent_int)
                away_percent = None

        # get opening lines
        consensus_container = consensus_columns[1]
        open_line_cells = consensus_container.find_all(class_="me-2")

        away_cell = open_line_cells[0]
        away_opens.append(away_cell.get_text())

        home_cell = open_line_cells[2]
        home_opens.append(home_cell.get_text())

    return pd.DataFrame({
                        'away_names':away_names, 
                        'away_lines':away_lines, 
                        'away_scores': away_scores,
                        'away_percents':away_percents,
                        'away_opens': away_opens,
                        'home_names': home_names, 
                        'home_lines':home_lines, 
                        'home_scores': home_scores, 
                        'home_percents': home_percents,
                        'home_opens': home_opens})