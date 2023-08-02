import numpy as np
import matplotlib.pyplot as plt
import scienceplots

plt.style.use(["science", "ieee"])

plt.rcParams.update({
    "figure.autolayout": True,
    "text.usetex": True,
    "font.family": "serif",
    "font.size": "16",
})


def key_to_label(key):
    digits = list(reversed(list(key)))
    label = "(" + ", ".join(digits) + ")"
    return label


def hist(ax, probs):
    x = list(range(len(probs.keys())))
    heights = np.array(list(probs.values()))
    keys = list(probs.keys())
    labels = list(map(key_to_label, keys))
    # Color the bars green
    ax.bar(x, heights, tick_label=labels, color="green")
    ax.tick_params(axis='x', rotation=90)
    ax.set_xlabel(r"EV Pick $x$")
    ax.set_ylabel(r"Probability $p(x)$")
