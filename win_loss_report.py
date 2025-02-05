from scipy.stats import norm
from scipy.stats import chisquare
import numpy as np
import pandas as pd

def win_loss_from_df(df):
    ct = pd.crosstab(df.fade, df.winner_ats)
    win_loss_report(ct.iloc[0,0] + ct.iloc[1,1], ct.iloc[0,1] + ct.iloc[1,0])
    print("\n")
    print(ct)

def win_loss_report(wins, losses, vig=1.1):
    win_pct = wins / (wins+losses)
    expected_wins = (wins + losses) /2
    std = np.sqrt(wins + losses)/2
    z_score = (wins-expected_wins) / std
    p_value = norm.cdf(z_score)
    profit_pct = 100 * (win_pct - (vig * (1-win_pct)))

    # betting markets are more like visa/mastercard. the side getting paid covers 
    # the cost for facilitating the transaction.

    # there isn't necessarily vig on the bet itself, because you are betting
    # against another person, not the house.

    # however, people who provide liquidity for the betting market want to make money 
    # for their troubles, so there is usually a little bit of vig.
     
    # On matchbook.com, this appears to be around .3%-.7% for NBA basketball. 
    # eg. [+102/-105.26] for spread or [-208/+205] for money line

    # On ProphetX (newish market, low volume), it is around .2% on big events
    # eg [-112/+111] on the superbowl ML right now
    # but closer to 1.2-1.7% on NBA: [-107/+102] --1.1%, [-103/-102] --1.2%, [100/-105] --1.2% 
    # [-101, -106] -- 1.7%

    # On novig (new market, almost no volume), they are like [-105/-104] - 2.2%, [+109/-127] - 3.7% 
    # [-108/-105] - 3%

    # I am estimating it at 1.7%.

    betting_market = (.97*wins) - (1.017 * losses)

    print(f"record:   {wins} - {losses}")
    if vig != 1.1:
        print(f"actual ({vig} vig) units: { round(wins - (vig*losses), 2)}")
    
    print(f"full vig (-110) units: { round(wins - (1.1*losses),2) }")
    print(f"reduced juice (-106) : { round(wins - (1.06 * losses),2) }")
    print(f"reduced juice (-105) : { round(wins - (1.05 * losses),2) }")
    print(f"betting market       : { round(betting_market, 2) }")

    print(f"win pct: {round(100 *win_pct,2)}%, expected wins: {expected_wins}")
    print(f"excess: {wins - expected_wins}, profit %: {round(profit_pct,2)}")
    print(f"z test: {round(z_score,2)}, std: {round(std,2)} , p-value: {round(1-p_value, 4)}")

