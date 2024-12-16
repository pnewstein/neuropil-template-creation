"""
simple script to segment out the neuropil
"""

from pathlib import Path
import json
from concurrent.futures import ProcessPoolExecutor

import nrrd
import click
import numpy as np
from skimage import morphology, restoration, filters, measure, measure
import pandas as pd

NO_FLIP = """! TYPEDSTREAM 2.4

affine_xform {
    xlate 0 0 0
    rotate 0 0 0
    scale 1 1 1
    shear 0 0 0
    center 0 0 0
}"""

Z_FLIP = """! TYPEDSTREAM 2.4

affine_xform {
    xlate 0 0 0
    rotate 0 0 0
    scale 1 1 -1
    shear 0 0 0
    center 0 0 0
}"""


def make_neuropil_mask(
    img_data: np.ndarray, scale: tuple[float, float, float]
) -> np.ndarray:
    """
    does image morphology manipulations to isolate the neuropils
    returns the processed image
    """
    assert len(img_data.shape) == 3
    filter_sigma = 0.1
    sigma = tuple(filter_sigma / e for e in scale)
    img_data_int_16 = img_data.astype(np.int16) * (
        0.9 * np.iinfo(np.int16).max / np.iinfo(img_data.dtype).max
    )
    blured = filters.gaussian(img_data_int_16, sigma)
    opening_size = 2
    size = tuple(opening_size / e for e in scale)
    kernel = restoration.ellipsoid_kernel(size, 1) != np.inf
    opened = morphology.opening(img_data, kernel)
    filter_sigma = 0.5
    sigma = tuple(filter_sigma / e for e in scale)
    blured = filters.gaussian(opened, sigma)
    threshold = filters.threshold_otsu(blured)
    neuropil_mask = blured > threshold
    return neuropil_mask.astype(np.uint8)

def invert_neuropil(metadata: dict, path: str, segmented: np.ndarray, invert: bool):
    inverted_metadata = metadata.copy()
    inverted_scale = inverted_metadata["spacings"].copy()
    del inverted_metadata["spacings"]
    if invert:
        inverted_scale[-1] = -inverted_scale[-1]
        (Path(path).parent / "flip.xform").write_text(Z_FLIP)
    else:
        (Path(path).parent / "flip.xform").write_text(NO_FLIP)
    inverted_metadata["space directions"] = np.diag(inverted_scale)
    nrrd.write(
        str(Path(path).parent / "inverted_neuropil_mask.nrrd"),
        segmented,
        compression_level=1,
        header={"spacings": inverted_scale},
    )


def process_one(path: str):
    img, metadata = nrrd.read(path)
    scale = metadata["spacings"]
    print(f"processing {path}")
    segmented = make_neuropil_mask(img, scale)
    nrrd.write(
        str(Path(path).parent / "neuropil_mask.nrrd"),
        segmented,
        compression_level=1,
        header={"spacings": scale},
    )
    # figure out where image is inverted
    sum_over_z = segmented.sum(axis=(0, 1))
    z_size = len(sum_over_z)
    frac_before = np.where(sum_over_z)[0][0] / z_size
    frac_after = 1 - (np.where(sum_over_z)[0][-1] / z_size)
    if frac_before > frac_after:
        # its inverted!
        invert_neuropil(metadata, path, segmented, True)
    else:
        invert_neuropil(metadata, path, segmented, False)
    # only get those neuropils taking up 95 percent of the neuropil volume
    thresh = .95
    labeled = measure.label(segmented)
    assert isinstance(labeled, np.ndarray)
    value_counts = pd.Series(labeled.ravel()).value_counts()
    npix_neuropils = value_counts.drop(0)
    frac_neuropils = npix_neuropils / npix_neuropils.sum()
    bad_inds = frac_neuropils.index[frac_neuropils<thresh]
    segmented[np.isin(labeled, bad_inds)] = 0
    return 0


@click.command()
@click.argument("paths-json", type=click.Path(exists=True))
def main(paths_json):
    paths = json.loads(Path(paths_json).read_text())
    print(paths)
    with ProcessPoolExecutor() as executor:
        map = executor.map(process_one, paths)
        assert all(m == 0 for m in map)


if __name__ == "__main__":
    main()
