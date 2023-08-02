import datetime
import os
import time

import matplotlib.pyplot as plt

import utils
from EV_knapsack import EV
from qaoa import QAOA
from plots import hist


def main():
    # List of EVs
    evs = [
        EV(time_required=[1, 2], power_required=[1, 1], max_power=1),
        EV(time_required=[1, 2], power_required=[1, 1], max_power=2),
        EV(time_required=[1, 1, 2], power_required=[1, 1, 1], max_power=2),
        EV(time_required=[1, 2, 3], power_required=[1, 2, 3], max_power=3),
        EV(time_required=[2, 3, 1, 1], power_required=[2, 2, 1, 1], max_power=4),
    ]

    # Problems in QAOA-CE
    # evs = [
    #     EV(time_required=[2, 1], power_required=[1, 1], max_power=1),
    #     EV(time_required=[1, 2], power_required=[1, 1], max_power=1),
    #     EV(time_required=[2, 1], power_required=[1, 1], max_power=2),
    #     EV(time_required=[2, 1], power_required=[2, 3], max_power=2),
    #     EV(time_required=[2, 1], power_required=[1, 2], max_power=2),
    # ]

    p = 3
    a = 10

    # Example: 2023-09-06_15:3:00
    outputs = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}"
    for ev, i in zip(evs, range(1, len(evs) + 1)):
        circuit = QAOA(ev, p)
        start = time.time()

        angles = utils.find_optimal_angles(circuit, ev, a)
        probs = utils.get_probs_dict(circuit, ev, angles, a)

        end = time.time()

        # Time in seconds
        time_taken = end - start

        bks = utils.best_known_solutions(ev)

        comments = [
            f"Considered {ev}",
            f"QAOA circuit with {p = } and {a = }",
            f"Optimized angles: {angles}",
            f"Resulting Probabilities: {probs}",
            f"Time taken: {time_taken} seconds",
            f"Best known solutions: {bks}",
            f"Higher the probability: {max(probs.values())} at reversed key: {max(probs, key=probs.get)[::-1]}",
            f"Higher the probability: {max(probs.values())} at key: {max(probs, key=probs.get)}"
        ]
        
        os.makedirs(f"outputs/{outputs}_{p}_{a}", exist_ok=True)
        file_name = f"{i}_result.txt"
        with open(os.path.join(f"outputs/{outputs}_{p}_{a}", file_name), "w") as f:
            f.write("\n".join(comments))

        fig, ax = plt.subplots()
        if ev.number_of_evs >= 4:
            fig.set_size_inches(16.5, 8.5)
        hist(ax, probs)
        plt.savefig(os.path.join(f"outputs/{outputs}_{p}_{a}", f"{i}_choice_hist.png"))
        plt.close()
    


if __name__ == "__main__":
    main()