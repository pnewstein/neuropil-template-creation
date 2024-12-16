"""
quickly plots the data
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import seaborn as sns
import pandas as pd
from scipy.stats import ttest_ind

def plotdata(ax: Axes, contrast: str, quant: pd.DataFrame, use_pcent:bool):
    if use_pcent:
        y = "percent " + contrast
    else:
        y = "count " + contrast
    if contrast == "in anti-hb-puncta zone":
        quant = quant.loc[~quant["used for anti-hb-puncta"]].copy()

    sns.barplot(quant, x="Condition", y=y, ax=ax, color="blue")
    sns.swarmplot(quant, x="Condition", y=y, ax=ax, color="gray")
    ax.set_xticks([0, 1], ["Control", "hb ME"])


def main():
    quant = pd.read_csv("quantification.csv", index_col=0)
    quant = quant.loc[quant["Condition"] != "Hb_presynapses"]
    contrasts = [c.split("count ")[-1] for c in quant.columns if c.startswith("count ")]
    for use_pcent in (True, False):
        fig, axs = plt.subplots(1, len(contrasts), constrained_layout=True)
        fig.set_size_inches((12, 5))
        sns.despine(fig)
        for contrast, ax in zip(contrasts, axs.ravel()):
            plotdata(ax, contrast, quant, use_pcent)
        if use_pcent:
            fig.savefig("barplot_pcent.svg")
        else:
            fig.savefig("barplot_num.svg")


main()
