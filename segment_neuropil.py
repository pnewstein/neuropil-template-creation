"""
simple script to segment out the neuropil
"""

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import nrrd
import click
import numpy as np
from skimage import morphology, restoration, filters

FLIP_XFORM = """! TYPEDSTREAM 2.4

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


def process_one(path: str):
    img, metadata = nrrd.read(path)
    scale = metadata["spacings"]
    print(f"processing {path}")
    # segmented = make_neuropil_mask(img, scale)
    # nrrd.write(
    # str(Path(path).parent / "neuropil_mask.nrrd"),
    # segmented,
    # compression_level=1,
    # header={"spacings": scale},
    # )
    # figure out where image is inverted
    segmented, _ = nrrd.read(str(Path(path).parent / "neuropil_mask.nrrd"))
    sum_over_z = segmented.sum(axis=(0, 1))
    z_size = len(sum_over_z)
    frac_before = np.where(sum_over_z)[0][0] / z_size
    frac_after = 1 - (np.where(sum_over_z)[0][-1] / z_size)
    if frac_before > frac_after:
        # its inverted!
        inverted_segmented = segmented[:, :, ::-1]
        nrrd.write(
            str(Path(path).parent / "inverted_neuropil_mask.nrrd"),
            inverted_segmented,
            compression_level=1,
            header={"spacings": scale},
        )
        (Path(path).parent / "init.xform").write_text(FLIP_XFORM)
    return 0


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def main(paths):
    for path in paths:
        process_one(path)
    quit()
    with ProcessPoolExecutor() as executor:
        map = executor.map(process_one, paths)
        assert all(m == 0 for m in map)


if __name__ == "__main__":
    main()
