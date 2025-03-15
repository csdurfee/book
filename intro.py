import numpy as np
import matplotlib.pyplot as plt
rng = np.random.default_rng(2718)
np.random.seed(2718)


def vig_vs_win_pct(max=10, step=.05):  
    vig_range = np.arange(1.0, max, step)

    break_even_point = 100 - (100/(1+vig_range))

    vig_label = -100 * vig_range

    plt.plot(vig_label, break_even_point)
    plt.gca().invert_xaxis()
    plt.ylabel("break-even percentage")
    plt.xlabel("vig")
    plt.grid()

def do_some_bets(skill = .5, payout=1000, vig=1.1, throw_one_out=False, 
                 random_fourth_bet=False, same_total_risk=True, num_parlays=100000,
                 silent=False):
    """
    Simulation of straight bets versus a 4 leg parlay.
    
    """

    if same_total_risk:
        one_straight_loss = 25
        one_straight_win = 25 / vig
    else:
        one_straight_loss = 100
        one_straight_win = 100 / vig

    straight_profit_loss = 0
    parlay_profit_loss = 0

    for b in range(num_parlays):
        bet1 = rng.random() < skill
        bet2 = rng.random() < skill
        bet3 = rng.random() < skill
        bet4 = rng.random() < skill

        if bet1 and bet2 and bet3 and bet4:
            parlay_profit_loss = parlay_profit_loss + payout
        else:
            parlay_profit_loss = parlay_profit_loss - 100

        for bet in [bet1, bet2, bet3]:
            # we are risking 25 on each bet, so the payout is less than 25.
            if bet:
                straight_profit_loss = straight_profit_loss + one_straight_win
            else:
                straight_profit_loss = straight_profit_loss - one_straight_loss

        if not random_fourth_bet:
            if throw_one_out:
                pass
            else:
                if bet4:
                    straight_profit_loss = straight_profit_loss + one_straight_win
                else:
                    straight_profit_loss = straight_profit_loss - one_straight_loss
        else:
            # what if the 4th bet is taken by flipping a coin?
            alt_bet4 = rng.random() < .5
            if alt_bet4:
                straight_profit_loss = straight_profit_loss + one_straight_win
            else:
                straight_profit_loss = straight_profit_loss - one_straight_loss

    ratio = straight_profit_loss/parlay_profit_loss
    if not silent:
        print(f"parlay: {parlay_profit_loss:,.2f}, straight: {straight_profit_loss:,.2f}, ratio: {ratio}")
    return (parlay_profit_loss, straight_profit_loss)

def parlay_vs_straight(skill=.55):
    parlay_wins = 0
    straight_wins = 0

    big_parlay_losses = 0
    big_straight_losses = 0

    parlays_made_money = 0
    straights_made_money = 0

    all_results = []

    for x in range(10000):
        results = do_some_bets(skill=skill, payout=1228.33, num_parlays=50, silent=True)
        if results[0] > results[1]:
            parlay_wins += 1
        elif results[1] > results[0]:
            straight_wins += 1

        if results[0] < -1000:
            big_parlay_losses += 1
        if results[1] < -1000:
            big_straight_losses += 1

        if results[0] > 0:
            parlays_made_money += 1
        if results[1] > 0:
            straights_made_money += 1
        
        all_results.append(results)

    print(f"parlay wins: {parlay_wins}, straight: {straight_wins}")
    print(f"parlay big losses: {big_parlay_losses}, straight big losses: {big_straight_losses}")
    print(f"parlays made money: {parlays_made_money}, straights: {straights_made_money}")
    return all_results