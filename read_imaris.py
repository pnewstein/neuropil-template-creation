"""
reads imaris files
"""

from pathlib import Path
import json

from h5py import Group
import numpy as np
import pandas as pd
from imaris_ims_file_reader.ims import ims, ims_reader
import napari
import nrrd
import click

BRP_LBLS = ["Brp", "Spots 1"]

def get_data_frames_from_hf(dset: Group) -> dict[str, pd.DataFrame]:
    """
    gets all of the imaris spots as data frames
    """
    out: dict[str, pd.DataFrame] = {}
    for item in dset.values():
        if "Spot" not in item.keys():
            continue
        df = pd.DataFrame(np.array(item["Spot"]))
        out[item.attrs["Name"][0].decode("utf-8")] = df.loc[
            :, ["PositionX", "PositionY", "PositionZ"]
        ]
    return out

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def main(paths):
    for path in paths:
        path = Path(path)
        folder_path = path.with_suffix("")
        folder_path.mkdir(exist_ok=True)
        ims_object = ims(path)
        assert isinstance(ims_object, ims_reader)
        data = ims_object[0, :, :, :, :]
        scale = ims_object.resolution
        (folder_path / "scale.json").write_text(json.dumps(scale[::-1]))
        assert ims_object.hf is not None
        dset = ims_object.hf["Scene8/Content"]
        assert isinstance(dset, Group)
        dfs = get_data_frames_from_hf(dset)
        print(list(dfs.keys()))
        brp_lbl = next(l for l in BRP_LBLS if l in dfs.keys())
        puncta_df = dfs[brp_lbl]
        print(puncta_df)
        puncta_df.to_csv(folder_path / "puncta.csv")
        for i in range(data.shape[0]):
            img_3d = data[i, :, :, :].transpose([2, 1, 0])
            nrrd.write(
                str(folder_path / f"chan{i}.nrrd"),
                img_3d,
                compression_level=1,
                header={"spacings": scale[::-1]},
            )
        ims_object.close()

def get_viewer_from_ims(path: Path):
    viewer = napari.Viewer()
    ims_object = ims(path)
    assert isinstance(ims_object, ims_reader)
    data = ims_object[0, :, :, :, :]
    viewer.add_image(data, scale=ims_object.resolution, channel_axis=0)
    assert ims_object.hf is not None
    dset = ims_object.hf["Scene8/Content"]
    assert isinstance(dset, Group)
    for name, df in get_data_frames_from_hf(dset).items():
        viewer.add_points(df, name=name, size=2)
    ims_object.close()


main()
