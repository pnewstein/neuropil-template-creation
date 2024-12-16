"""
Gets image spots from imaris
"""

from pathlib import Path
import json

from imaris_ims_file_reader.ims import ims, ims_reader
from h5py import Group
import pandas as pd
import numpy as np
import click
import xform
import nrrd

BRP_LBLS = ["Brp", "Spots 1"]

def in_mask(pixel_df: pd.DataFrame, mask: np.ndarray) -> np.ndarray:
    """
    gets a boolean array for each coordinate being in the mask
    """
    off_the_charts = (
        (pixel_df["PositionX"] < -1)
        | (pixel_df["PositionX"] > mask.shape[0])
        | (pixel_df["PositionY"] < -1)
        | (pixel_df["PositionY"] > mask.shape[1])
        | (pixel_df["PositionZ"] < -1)
        | (pixel_df["PositionZ"] > mask.shape[2])
    )
    in_neuropil_mask = mask.astype(bool)[
        pixel_df["PositionX"].clip(0, mask.shape[0] - 1),
        pixel_df["PositionY"].clip(0, mask.shape[1] - 1),
        pixel_df["PositionZ"].clip(0, mask.shape[2] - 1),
    ]
    return in_neuropil_mask & (~off_the_charts)

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def main(paths):
    affine_path = Path("flip.xform")
    for path in paths:
        path = Path(path)
        ims_object = ims(path)
        assert isinstance(ims_object, ims_reader)
        hf = ims_object.hf
        assert hf is not None
        dset = hf["Scene8/Content"]
        assert isinstance(dset, Group)
        dfs: dict[str, pd.DataFrame] = {}
        for item in dset.values():
            if "Spot" not in item.keys():
                continue
            df = pd.DataFrame(np.array(item["Spot"]))
            dfs[item.attrs["Name"][0].decode("utf-8")] = df.loc[
                :, ["PositionX", "PositionY", "PositionZ"]
            ]
        if len(dfs) == 1:
            brp_lbl = next(iter(dfs.keys()))
        else:
            brp_lbl = next(l for l in BRP_LBLS if l in dfs.keys())
        puncta_df = dfs[brp_lbl]
        anon_key = json.loads(Path("image_key.json").read_text())
        dir_prefix = next(k for k, v in anon_key.items() if v in path.name)
        dir_name, = [p for p in Path().glob(f"{dir_prefix}*") if p.is_dir()]
        puncta_df.to_csv(Path(dir_name) / "all_reformated_puncta.csv")
        # get mirror image of the pixels
        mirror_xform = -xform.CMTKtransform(affine_path)
        flipped_puncta = pd.DataFrame(mirror_xform.xform(np.array(puncta_df)), columns=puncta_df.columns)
        flipped_puncta.to_csv(Path(dir_name) / "all_fliped_puncta.csv")
        scale = np.array([0.071] * 3)
        # subset to those pixels within the neuropil
        reformat_neuropil, _ = nrrd.read(Path(dir_name) / "neuropil_mask.reformat.nrrd")
        pixel_puncta_df = np.round(puncta_df / scale).astype(int)
        in_img_neuropil = in_mask(pixel_puncta_df, reformat_neuropil)
        template, _ = nrrd.read(Path(dir_name) / "neuropil_mask.reformat.nrrd")
        pixel_flipped_df = np.round(flipped_puncta / scale).astype(int)
        in_template = in_mask(pixel_puncta_df, template) | in_mask(pixel_flipped_df, template)
        in_neuropil = in_template & in_img_neuropil
        (puncta_df[in_neuropil]).to_csv(Path(dir_name) / "reformated_puncta.csv")
        (flipped_puncta[in_neuropil]).to_csv(Path(dir_name) / "fliped_puncta.csv")
        

if __name__ == "__main__":
    main()
