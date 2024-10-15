from pathlib import Path
import json

import xform
from h5py import File, Group
import numpy as np
import pandas as pd
import nrrd


def main():
    for path in Path().glob("**/puncta.csv"):
        scale = json.loads((path.parent / "scale.json").read_text())
        this_xform = -xform.CMTKtransform(path.parent / "affine.xform")
        image_brp = pd.read_csv(path, index_col=0)
        neuropil_mask, _ = nrrd.read(str(path.parent / "neuropil_mask.nrrd"))
        image_brp_pixels = (image_brp / scale).round().astype(int)
        in_neuropil_mask = neuropil_mask.astype(bool)[
            image_brp_pixels["PositionX"].clip(0, neuropil_mask.shape[0] - 1),
            image_brp_pixels["PositionY"].clip(0, neuropil_mask.shape[1] - 1),
            image_brp_pixels["PositionZ"].clip(0, neuropil_mask.shape[2] - 1),
        ]

        template_brp = this_xform.xform(np.array(image_brp.loc[in_neuropil_mask, :]))
        out_df = pd.DataFrame(template_brp, columns=image_brp.columns)
        out_df.to_csv(path.parent / "reformated_puncta.csv")



if __name__ == "__main__":
    main()
