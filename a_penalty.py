import datetime
import os
import time
import numpy as np

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

    utils.is_adding_noise_model = False
    os.makedirs("ratio", exist_ok=True)
        
    # Test for simulated quantum circuit
    # for a in np.arange(0, 12, 2):
    #     ratio = ""
    #     for ev, i in zip(evs, range(1, len(evs) + 1)):  
    #         sim_circuit = QAOA(ev, p)
    #         ratio = utils.approximation_ratio(sim_circuit, ev, p, a)
    #         print(f"{p = }: ratio = {ratio}")
    #         comment = f"""a-dependence of LinQAOA approach.
    #                     Problem: {ev}
    #                     Parameters: {p = }.
    #                     Calculated approximation ratios: {ratio},
    #                     """
    #         with open(f"ratio/{a}_{i}_penalty_{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}.txt", "w") as f:
    #             f.write(comment)

    # Test for real quantum circuit
    for ev, i in zip(evs, range(1, len(evs) + 1)):
        circuit = QAOA(ev, p)
        qc_circuit = QAOA(ev, p, verbose=False) # for real quantum circuit

        angles = utils.find_optimal_angles(circuit, ev, a)
        ratio = utils.approximation_ratio_on_real_device(qc_circuit, ev, angles, p, a)

        print(f"{p = }, {i = }, {ratio = }")

if __name__ == "__main__":
    main()