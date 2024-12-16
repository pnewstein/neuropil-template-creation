"""
This compares the reformated neuropil mask to the template
brain to see how well the transformation worked
"""

from pathlib import Path

import nrrd
import pandas as pd
import numpy as np


def reindex(quant: pd.DataFrame):
    """
    splits out metadata from the file name and gives an easier index to read
    adds columns Condition idx file_name
    """
    fn_prefix = [s.split("--")[0] for s in quant.index]
    metadata_df = pd.DataFrame(
        [s.split("-") for s in fn_prefix],
        columns=np.array(["Condition", "idx"]),
        index=quant.index,
    )
    merged = pd.concat((metadata_df, quant), axis=1)
    merged["file_name"] = merged.index
    merged.index = fn_prefix
    return merged


def main():
    template, _ = nrrd.read("template.nrrd")
    template_mask = template == 254
    max_score = 2 * template_mask.sum()
    seriess: list[pd.Series] = []
    for reformated_path in Path().glob("**/neuropil_mask.reformat.nrrd"):
        reformated, _ = nrrd.read(str(reformated_path))
        sum_template_covered = (reformated[template_mask] > 0).sum()
        sum_reformat_covered = (template[reformated > 0] > 128).sum()
        seriess.append(
            pd.Series(
                {
                    "template_covered": sum_template_covered,
                    "reformate_covered": sum_reformat_covered,
                },
                name=str(reformated_path.parent),
            )
        )
    df = pd.DataFrame(seriess)
    df["score"] = (df["template_covered"] + df["reformate_covered"]) / max_score

    df = reindex(df)
    df.to_csv("xform_qual.csv")


if __name__ == "__main__":
    main()
