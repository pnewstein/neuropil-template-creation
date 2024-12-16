"""
this code anonymizes experimental (with control) data and moves files to a new directory for downstream processing
"""

import string
from pathlib import Path
import json

import pandas as pd
import numpy as np
import tifffile
import nrrd

score_thresh = .8

out_dir = Path("export")
hb_presynapse_channel = "chan3.reformat.nrrd"
other_channel = "chan0.reformat.nrrd"

def main():
    out_dir.mkdir(exist_ok=True)
    df = pd.read_csv("xform_qual.csv", index_col=0)
    df = df.loc[df["score"] > score_thresh]
    eg_names = [l1 + l2 for l1 in string.ascii_lowercase for l2 in string.ascii_lowercase]
    hb_presynapse = df.loc[df["Condition"] == "Hb_presynapses"]
    hb_presynapse["anon"] = [f"{i:02}" for i, _ in enumerate(hb_presynapse.index, 1)]
    hb_presynapse["puncta_file"] = hb_presynapse_channel
    other = df.loc[df["Condition"] != "Hb_presynapses"]
    shuffled = other.sample(frac=1)
    shuffled["anon"] = eg_names[:len(shuffled)]
    shuffled["puncta_file"] = other_channel
    df_with_anon = pd.concat((shuffled, hb_presynapse), join="outer")
    assert not np.any(df_with_anon.isna())
    anon = df_with_anon["anon"].to_dict()
    Path("image_key.json").write_text(json.dumps(anon, indent=2))
    for _, row in df_with_anon.iterrows():
        fn = row["file_name"]
        assert isinstance(fn, str)
        path = Path(fn) / row["puncta_file"]
        data, _ = nrrd.read(path)
        tifffile.imwrite(out_dir / (row["anon"] + ".tif"), data.T, imagej=True, metadata={
            "spacing": 0.071,
            "axes": "ZYX"
        })

if __name__ == "__main__":
    main()
