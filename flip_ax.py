"""
this code is to flip inverted templates and flip.xforms
"""

from pathlib import Path
import sys

import nrrd
from segment_neuropil import Z_FLIP, NO_FLIP, invert_neuropil


def invert_axis(folder: Path):
    flip_xform_path = folder / "flip.xform"
    old_xform = flip_xform_path.read_text()
    if old_xform == Z_FLIP:
        new_xform = NO_FLIP
    elif old_xform == NO_FLIP:
        new_xform = Z_FLIP
    else:
        assert False
    inverted_mask_path = str(folder / "inverted_neuropil_mask.nrrd")
    data, metadata = nrrd.read(inverted_mask_path)
    invert_neuropil(metadata, inverted_mask_path, data, True)
    flip_xform_path.write_text(new_xform)


def main():
    idx = Path(sys.argv[-1]).read_text().splitlines()
    paths = [
        p
        for p in Path().iterdir()
        if p.name.split("--")[0].split("-")[-1] in idx and p.is_dir()
    ]
    for path in paths:
        print(path)
        invert_axis(path)

if __name__ == "__main__":
    main()

