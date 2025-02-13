### generate a list of A's, B's, and F's.
### then show that they will have different records.
import pandas as pd
import numpy as np

from io import StringIO

class BetGrading:
    def __init__(self):
        self.rng = np.random.default_rng(2718)

        # number of bets in each simulated betting record
        self.df_size = 500

        # win rate for each category of bet
        self.thresholds = {
            'A': .60,
            'B': .57,
            'F': .54
        }

        # how often each category comes up
        self.grade_frequencies = {
            'A': .2,
            'B': .3,
            'F': .5
        }

        # how many 'units' to bet on each category.
        self.units_map = {
            'A': 3,
            'B': 2,
            'F': 1
        }

        self.scramble_frequency = 0

    def create_df(self, num_bets):
        results = []
        grades = self.rng.choice(list(self.grade_frequencies.keys()), 
                                 size=num_bets, 
                                 p=list(self.grade_frequencies.values()))
        for x in range(num_bets):
            grade = grades[x]
            if self.rng.random() < self.thresholds[grade]:
                results.append("W")
            else:
                results.append("L")

        graded_df = pd.DataFrame(dict(grades=grades, result=results))

        return graded_df


    def score_bets_with_grade(self, base_df):
        record = base_df.groupby("grades").value_counts()
        units_won = 0
        for grade in self.units_map.keys():
            try:
                _wins = record[grade]['W']
            except KeyError:
                _wins = 0
                print("keyerror")

            try:
                _losses = record[grade]['L']
            except KeyError:
                _losses = 0

            net_wins = _wins - (1.1 * _losses)
            units_won += (net_wins * self.units_map[grade])

        # rounding prevents ugly floating point stuff
        return round(units_won,2)


    def get_unit_multiplier(self, base_df):
        # average number of units bet
        actual_frequencies = base_df.grades.value_counts() / len(base_df.grades)
        # TODO: should thie be theoretical frequencies instead?

        #return (pd.Series(self.units_map) * actual_frequencies).sum()
        return (pd.Series(self.units_map) * pd.Series(self.grade_frequencies)).sum()

    def score_bets_normally(self, base_df, unit_multiplier=None):


        record = base_df.groupby("grades").value_counts()
        try:
            total_wins = record[:,'W'].sum()
        except KeyError:
            total_wins = 0
        try:
            total_losses = record[:,'L'].sum()
        except KeyError:
            total_losses  = 0

        units_won = total_wins - (1.1 * total_losses)

        if unit_multiplier is None:
            unit_multiplier = self.get_unit_multiplier(base_df)
            #print(unit_multiplier) 
        # rounding prevents ugly floating point stuff
        return round(unit_multiplier * units_won, 2)    

    def graded_vs_ungraded(self, perturb=False):
        grade_wins = 0
        grade_losses = 0
        grade_ties = 0
        diffs = []
        losses = []

        for x in range(1000):
            base_df = self.create_df(self.df_size)
            multi = self.get_unit_multiplier(base_df)
                
            with_grade = self.score_bets_with_grade(base_df)

            normally = self.score_bets_normally(base_df)
            
            if with_grade == normally:
                grade_ties += 1
            elif with_grade > normally:
                grade_wins += 1
            else:
                grade_losses += 1
                losses.append(base_df)
            diffs.append(with_grade - normally)

        print(f"wins: {grade_wins}, losses: {grade_losses}, ties: {grade_ties}")
        print(f"mean diff: { np.mean(diffs) }")
        return diffs, losses

    def test_some_grades(self, n, df_size, num_to_scramble):
        good = []
        bad = []
        normal = []
        fraction_agree = []

        for x in range(n):
            bets = self.create_df(df_size)

            normal_score = self.score_bets_normally(bets) 
            normal.append(normal_score)

            good_score = self.score_bets_with_grade(bets)
            good.append(good_score)

            # Simulate imperfect grading
            bad_grading = bets.copy()

            # I'm not sure what a reasonable number of each class is to change.
            # seems like it should match proportion of actual sample.
            ### select indexes to change

            idx_to_change = np.random.choice(bets.index, num_to_scramble)
            vals_to_change = np.random.choice(['A', 'B', 'F'], num_to_scramble, p=[.2,.3,.5])

            ## just randomly pick 30% of the rows, blank them out,
            ## then fill them back in with random weighted selections of F/B/A

            bad_grading.loc[idx_to_change, 'grades'] = vals_to_change

            #print(f"changed {sum(bets.grades != bad_grading.grades)}")
            fraction_agree.append(sum(bad_grading.grades == bets.grades) / len(bets))

            bad_score = self.score_bets_with_grade(bad_grading)
            bad.append(bad_score)
        return pd.DataFrame({'good': good, 'bad': bad, 'flat': normal, 
                             'fraction_agree': fraction_agree})
