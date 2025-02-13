import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class RandomWalk:
    def __init__(self):
        self.rng = np.random.default_rng(2718)
        self.VIG = -1.1

    def plot_random_walk(self, p, n=1000):
        fig, axs = plt.subplots(3,3, sharey='all')
        plt.suptitle(f"random walk with p={p}")
        for x in range(3):
            for y in range(3):
                win_or_lose = (np.random.rand(n) < p).astype("float")
                win_or_lose[win_or_lose==0] = self.VIG
                random_walk = np.cumsum(win_or_lose)
                axs[x,y].plot(random_walk)
                axs[x,y].axhline(0)

    def generate_alternating(self, skill_levels, determinate=False, period_length=100, periods=10):
        assert len(skill_levels) == 2, "must have 2 skill levels."

        base_data = []
        ticks_up = []
        ticks_down = []

        prev_skill = skill_levels[0]
        for x in range(periods):
            # every `period_length` days, the skill level can change.
            if determinate:
                # take the other one. not the nicest way to do it.
                skill_copy = skill_levels.copy()
                skill_copy.remove(prev_skill)
                current_skill = skill_copy[0]
            else:
                current_skill = np.random.choice(skill_levels)

            # mark every time we switch skill_levels
            if current_skill != prev_skill:
                if current_skill > prev_skill:
                    ticks_up.append(x * period_length)
                elif current_skill < prev_skill:
                    ticks_down.append(x * period_length)
            # if the random value is less than the skill level, it's a win, otherwise it's a loss
            win_or_lose = (np.random.rand(period_length) < current_skill).astype("float")
            
            # step back by VIG amount on losses
            win_or_lose[win_or_lose==0] = self.VIG
            base_data.extend(win_or_lose)

            prev_skill = current_skill

        return [np.cumsum(base_data), ticks_up, ticks_down]

    def plot_random_walk2(self, random_walks, show_partitions=False, ticks_up=None, ticks_down=None):
        fig, axs = plt.subplots(3,3, sharey='all')

        walk_counter = 0
        first_axis = None
        for x in range(3):
            for y in range(3):
                axs[x,y].set_ylim(bottom=-50, top=100)
                axs[x,y].set_xticks([])
                axs[x,y].plot(random_walks[walk_counter][0])
                axs[x,y].axhline(0)
                if show_partitions:
                    axs[x,y].vlines(random_walks[walk_counter][1], 0,50, 'g')
                    axs[x,y].vlines(random_walks[walk_counter][2], 0, 50, 'r')   
                walk_counter += 1
        plt.figure(figsize=(8,8)) # FIXME: this isn't working to make the image bigger.
    