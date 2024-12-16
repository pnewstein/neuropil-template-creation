"""
reads imaris files
"""

from pathlib import Path
import json
import shutil

from h5py import Group
import numpy as np
import pandas as pd
from imaris_ims_file_reader.ims import ims, ims_reader
import napari
import nrrd
import click

    

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def main(paths):
    for path in paths:
        path = Path(path)
        folder_path = path.with_suffix("")
        try:
            ims_object = ims(path)
        except AttributeError:
            click.echo(f"failed on {path}")
        assert isinstance(ims_object, ims_reader)
        data = ims_object[0, :, :, :, :]
        scale = ims_object.resolution
        folder_path.mkdir(exist_ok=True)
        (folder_path / "scale.json").write_text(json.dumps(scale[::-1]))
        for i in range(data.shape[0]):
            img_3d = data[i, :, :, :].transpose([2, 1, 0])
            nrrd.write(
                str(folder_path / f"chan{i}.nrrd"),
                img_3d,
                compression_level=1,
                header={"spacings": scale[::-1]},
            )
        ims_object.close()


if __name__ == "__main__":
    main()
