"""
makes a csv file of puncta counts in each condition
"""

from pathlib import Path

import pandas as pd
import nrrd


def main():
    """
    makes a csv file of puncta counts in each condition
    columns are
        total
            The total number of puncta in the image
        in neuropil
            The number of puncta that are in the template neuropil
        in hb-punca zone
            The number of puncta that are in the zone annotated as high in hb filtered punca
        in anti-hb-puncta zone
            The number of puncta that are in the zone annotated as low in hb filtered punca
    """
    serieses: list[pd.Series] = []
    for path in Path().glob("**/reformated_puncta.csv"):
        neuropil_spots = pd.read_csv(path, index_col=0)
        original_spots_path = path.parent / "puncta.csv"
        original_spots = pd.read_csv(original_spots_path, index_col=0)
        hb_image, hb_metadata = nrrd.read("hb_puncta_mask.nrrd")
        pix_spots = (neuropil_spots / hb_metadata["spacings"]).round().astype(int)
        in_hb_image = hb_image.astype(bool)[
            pix_spots["PositionX"],
            pix_spots["PositionY"],
            pix_spots["PositionZ"],
        ]
        not_hb_image, not_hb_metadata = nrrd.read("hb_puncta_anti_mask.nrrd")
        assert all(
            a == b for a, b in zip(not_hb_metadata["spacings"], hb_metadata["spacings"])
        )
        in_not_hb_image = not_hb_image.astype(bool)[
            pix_spots["PositionX"],
            pix_spots["PositionY"],
            pix_spots["PositionZ"],
        ]
        serieses.append(
            pd.Series(
                {
                    "total": len(original_spots),
                    "in neuropil": len(neuropil_spots),
                    "in hb-puncta zone": in_hb_image.sum(),
                    "in anti-hb-puncta zone": in_not_hb_image.sum(),
                },
                name=path.parent,
            )
        )
    df = pd.DataFrame(serieses)
    df.to_csv("quantification.csv")

if __name__ == "__main__":
    main()
