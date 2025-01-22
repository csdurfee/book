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

    print(f"record:   {wins} - {losses}")
    if vig != 1.1:
        print(f"actual units: {wins - (vig*losses)}")
    else:
        print(f"full vig (-110) units: { round(wins - (1.1*losses),2) }")
        print(f"reduced juice (-106) : { round(wins - (1.06 * losses),2) }")


    print(f"win pct: {round(100 *win_pct,2)}%, expected wins: {expected_wins} , excess: {wins - expected_wins}, profit %: {round(profit_pct,2)}")
    print(f"z test: {z_score}, std: {std} , p-value: {1-p_value}")

