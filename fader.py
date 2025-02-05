
import pandas as pd

import datetime

import scrape_sbr


def daily_picks():
    # make sure we've got yesterday's data on disk
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(1)
    scrape_sbr.fetch_data_range(yesterday, yesterday)
    

    # fetch data for today but don't cache on disk (because games haven't happened yet!)
    today_data = get_today_data()
    ats_by_date = get_today_ats()

    return superfade(base_picks=today_data, ats_record=ats_by_date)


def get_today_ats(window=None):
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    yesterday = now - datetime.timedelta(1)
    ## NOTE: this is using default window= value which is None (all time records.)
    ats_by_date = scrape_sbr.get_ats_for_range("2024-10-22", today, window=window)

    # FIXME: this is hacky but get_ats_for_range reads off of disk
    # and I don't want to store today's data from before the games are done.
    ats_by_date[today] = ats_by_date[yesterday.strftime("%Y-%m-%d")]
    return ats_by_date

def get_today_data():
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    today_data = scrape_sbr.get_for_date(now.year, now.month, now.day, 
                                         save_csv=False)
    today_data['game_date'] = today
    return today_data



def fade_the_public(lower_thresh = 50, upper_thresh=60, games=None):
    if games is None:
        games = scrape_sbr.clean_data()
    games['fade'] = None
    
    # drop games where we don't have betting percents
    df = games[~(games.away_percents == "-")]

    below_thresh = df.away_percents < lower_thresh
    above_thresh = df.away_percents > upper_thresh

    df['fade_pick'] = None
    df['fade_vs'] = None

    ## select home vs. away for the fade pick, and fill in the names
    # if the away_percents is below the threshold, take "AWAY"
    df.loc[below_thresh, 'fade'] = "AWAY"
    df.loc[below_thresh, 'fade_pick'] = df.loc[below_thresh, 'away_names']
    df.loc[below_thresh, 'fade_vs'] = df.loc[below_thresh, 'home_names']
    
    # else, if away_percents is above the threshold, take "HOME"
    df.loc[above_thresh, 'fade'] = "HOME"
    df.loc[above_thresh, 'fade_pick'] = df.loc[above_thresh, 'home_names']
    df.loc[above_thresh, 'fade_vs'] = df.loc[above_thresh, 'away_names']

    # drop rows where it's 50-50. these might be interesting at some point.
    return df[df.away_percents != 50].copy()


def superfade(eliminate_top=5, lower_thresh=49, upper_thresh=60, base_picks=None,
              ats_record=None, window=20, dir='sbr'):
    """
    This is the "fade the public" strategy but filtering out teams that are good/bad vs the spread
    """
    if base_picks is None:
        base_picks = fade_the_public(lower_thresh, upper_thresh)
    else:
        base_picks = fade_the_public(lower_thresh, upper_thresh, games=base_picks)

    good_picks = []

    if ats_record is not None:
        ats_by_date = ats_record
    else:

        max_date = base_picks.game_date.max()
        min_date = base_picks.game_date.min()
        # 'window' indicates how many previous days to go back for ATS records (eg last 30 days)
        # None indicates use the whole season


        ### FIXME: this shouldn't use the 'dir' argument. pass in the base_picks.
        ats_by_date = scrape_sbr.get_ats_for_range(start=min_date, end=max_date, dir=dir, window=window) 
    # note: this isn't ideal, we're getting days we don't need to 
    prev_day = None
    for (d, ats) in ats_by_date.items():
        # we have to lag by one day here so we're not using today's standings to bet on 
        # today's results.
        if prev_day is None:
            prev_day = ats
            continue # we have to skip the first day
        else:
            if eliminate_top < 1:
                ### option 1. filter by win percentage
                top_ats_teams = prev_day[prev_day.ats_win_pct > eliminate_top].sort_values('ats_win_pct', ascending=False)
                bottom_ats_teams = prev_day[prev_day.ats_win_pct < (1 - eliminate_top)].sort_values('ats_win_pct', ascending=False)

            else:
                ### option 2: filter by top n teams and bottom _n_teams
                top_ats_teams = prev_day.sort_values('ats_win_pct', ascending=False)[:eliminate_top]
                bottom_ats_teams = prev_day.sort_values('ats_win_pct',ascending=True)[:eliminate_top]
            
            # don't pick against the teams with the best recordw against the spread.
            # don't pick for teams with the worst records against the spread.
            sel = (base_picks.game_date == d) & (~base_picks.fade_vs.isin(top_ats_teams.index) & \
                                                  (~base_picks.fade_pick.isin(bottom_ats_teams.index)))

            today_picks = base_picks[sel]
            good_picks.append(today_picks)
            prev_day = ats

        superfade = pd.concat(good_picks, ignore_index=True)
    return superfade.dropna(subset=['fade'])


def superfade_money(base_picks, dir, eliminate_top=3):
    ### FIXME: thresholds hardcoded
    base_picks = fade_the_public(49,60, games=base_picks)

    ### get starting and ending dates for range from base_picks.
    max_date = base_picks.game_date.max()
    min_date = base_picks.game_date.min()

    good_picks = []

    ## FIXME: get_money_for_range should have base_picks passed in 'dir' argument bad!!!!!!
    money_by_date = scrape_sbr.get_money_for_range(start=min_date, end=max_date, dir=dir)
    for (d, money) in money_by_date.items():
        # find the good picks on this day alone
        top_money_teams = money.sort_values(ascending=False)[:eliminate_top]
        exclude = top_money_teams.keys()
        #print(f"excluding {exclude}")

        #FIXME; this isn't right
        # throwing out picks where we're taking the home team, but they're too popular.
        #sel = (base_picks.game_date == d) & (~(base_picks.home_names.isin(exclude) & (base_picks.fade == "HOME")  ))
        sel = (base_picks.game_date == d) & (~(base_picks.home_names.isin(exclude)))
        today_picks = base_picks[sel]
        good_picks.append(today_picks)
    superfade = pd.concat(good_picks, ignore_index=True)
    return superfade         


    # I experimented with filtering by top/bottom teams by money, but it didn't work as well
    # as record ATS.

    """
    ### tried using a window of top money teams, but it didn't work as well, and goes
    ### against the basic premise that the lines overvalue some teams.
    else:
        # doing it the 'honest' way. at each day, we use the top money teams up to that
        # point in the season to filter.
        good_picks = []
        # FIXME: next line should use the range contained in base_picks, so it can be passed in for this strat
        money_by_date = scrape_sbr.get_money_for_range()
        for (d, money) in money_by_date.items():
            # find the good picks on this day alone
            top_money_teams = money.sort_values(ascending=False)[:eliminate_top]
            exclude = top_money_teams.keys()
            #print(f"excluding {exclude}")

            #FIXME; this isn't right
            # throwing out picks where we're taking the home team, but they're too popular.
            #sel = (base_picks.game_date == d) & (~(base_picks.home_names.isin(exclude) & (base_picks.fade == "HOME")  ))
            sel = (base_picks.game_date == d) & (~(base_picks.home_names.isin(exclude)))
            today_picks = base_picks[sel]
            good_picks.append(today_picks)

        superfade = pd.concat(good_picks, ignore_index=True)
    """

def analyze_fade(df):

    win_counts = df[df.winner_ats == df.fade].fade_pick.value_counts()
    lose_counts = df[df.winner_ats != df.fade].fade_pick.value_counts()

    win_against_counts = df[df.winner_ats == df.fade].fade_vs.value_counts()
    lose_against_counts = df[df.winner_ats != df.fade].fade_vs.value_counts()

    super_df = pd.DataFrame({'win': win_counts,
                              'lose': lose_counts,
                              'wins_against': win_against_counts,
                              'losses_against': lose_against_counts}).fillna(0)

    # you can't actually do .astype() in place, above
    super_df['win']  = super_df['win'].astype(int)
    super_df['lose'] = super_df['lose'].astype(int)
    super_df['wins_against'] = super_df['wins_against'].fillna(0).astype(int)
    super_df['losses_against'] = super_df['losses_against'].fillna(0).astype(int)


    super_df['win_pct'] = super_df.win / (super_df.win + super_df.lose)
    super_df['units'] = super_df.win - (1.1 * super_df.lose)

    super_df['win_units_against'] = super_df.wins_against - (1.1 * super_df.losses_against)


    super_df['total_units'] = super_df['units'] + super_df['win_units_against']

    return super_df