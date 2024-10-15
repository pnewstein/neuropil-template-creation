"""
simple script to segment out the neuropil
"""

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import nrrd
import click
import numpy as np
from skimage import morphology, restoration, filters


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
    segmented = make_neuropil_mask(img, scale)
    nrrd.write(
        str(Path(path).parent / "neuropil_mask.nrrd"),
        segmented,
        compression_level=1,
        header={"spacings": scale},
    )
    return 0

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
def main(paths):
    with ProcessPoolExecutor() as executor:
        map = executor.map(process_one, paths)
        assert all(m == 0 for m in map)



if __name__ == "__main__":
    main()
