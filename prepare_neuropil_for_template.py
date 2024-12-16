"""
reformates all of the paths
"""

import sys
from pathlib import Path
import json
from subprocess import run

import numpy as np
import nrrd


def main():
    idx = Path(sys.argv[-1]).read_text().splitlines()
    paths = [
        p
        for p in Path().iterdir()
        if p.name.split("--")[0].split("-")[-1] in idx and p.is_dir()
    ]
    print(paths)
    for path in paths:
        print(path)
        inverted_mask_path = path / "inverted_neuropil_mask.nrrd"
        data, metadata = nrrd.read(str(inverted_mask_path))
        scale = metadata["spacings"]
        (axes,) = np.where(scale < 0)
        data = np.flip(data, axis=axes)
        nrrd.write(
            str(path / "for_template.nrrd"), data, header={"spacings": np.abs(scale)}
        )


def view():
    import napari

    viewer = napari.Viewer()
    for path in Path().glob("**/upright.nrrd"):
        data, md = nrrd.read(str(path))
        viewer.add_labels(data, scale=md["spacings"], name=path.parent)


if __name__ == "__main__":
    main()
