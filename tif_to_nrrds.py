"""
converts a folder of tifs to a folder of nrrds
"""

from pathlib import Path

from tifffile import TiffFile
import nrrd
import click
import numpy as np
from skimage import morphology, restoration, filters


def _xy_voxel_size(tags, key):
    assert key in ["XResolution", "YResolution"]
    if key in tags:
        num_pixels, units = tags[key].value
        return units / num_pixels
    # return default
    return 1.0


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
    return neuropil_mask.astype(np.uint8) * 255


@click.command(help="convers a list of tifs to folders of nrrds")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--channel", type=int, default=0, help="channel to make binary")
def main(paths, channel):
    for path in paths:
        path = Path(path)
        folder_path = path.with_suffix("")
        folder_path.mkdir(exist_ok=True)
        with TiffFile(path) as tif:
            series = tif.series[0]
            axes = series.get_axes()
            assert axes == "ZCYX"
            data = series.asarray()
            assert tif.imagej_metadata is not None
            zdim = tif.imagej_metadata.get("spacing", 1.0)
            first_page = series.pages[0]
            assert first_page is not None
            ydim = _xy_voxel_size(first_page.tags, "YResolution")
            xdim = _xy_voxel_size(first_page.tags, "XResolution")
        for i in range(data.shape[1]):
            img_3d = data[:, i, :, :].transpose([2, 1, 0])
            click.echo(f"writing channel {i} of {path}", err=True)
            if i == channel:
                mask = make_neuropil_mask(img_3d, scale=(xdim, ydim, zdim), pixel_size=.2)
                nrrd.write(
                    str(folder_path / f"02neuropil_mask.nrrd"),
                    mask,
                    compression_level=1,
                    header={"spacings": [xdim, ydim, zdim]},
                )
            nrrd.write(
                str(folder_path / f"chan{i}.nrrd"),
                img_3d,
                compression_level=1,
                header={"spacings": [xdim, ydim, zdim]},
            )


if __name__ == "__main__":
    main()
