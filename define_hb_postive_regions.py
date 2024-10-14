from pathlib import Path
from functools import lru_cache

import napari
import nrrd
import pandas as pd
import numpy as np
import scipy.ndimage as ndi


DOWNSCALE_FACTOR = 1

image, metadata = nrrd.read("template.nrrd")
viewer = napari.Viewer()
scale = metadata["spacings"]
viewer.add_image(image, scale=scale, name="template")
dfs: list[pd.DataFrame] = []
for path in Path().glob("**/reformated_puncta.csv"):
    spots = pd.read_csv(path, index_col=0) 
    viewer.add_points(spots, name=path.parent.name)
    dfs.append(spots)
all_spots = pd.concat(dfs)
working_scale = [s * DOWNSCALE_FACTOR for s in scale]
pix_spots = (all_spots / working_scale).round().astype(int)
assert isinstance(pix_spots, pd.DataFrame)
pix_count_volume = np.zeros(tuple(s//DOWNSCALE_FACTOR for s in image.shape)).astype(np.uint8)
for _, (x, y, z) in pix_spots.iterrows():
    pix_count_volume[x, y, z] += 1
max_pix_count = pix_count_volume.max()
assert max_pix_count < 100, "maybe overflow happend"
pix_count_volume *= 255 // max_pix_count

@lru_cache
def get_blured(sigma):
    return ndi.gaussian_filter(pix_count_volume.astype(float), sigma)

def make_regions(connectedness: float, fraction_in: float):
    """
    this function defines a region what includes fraction_in of the points
    it adds a new layer to the napari viewer and saves a nrrd 

    increasing connectedness tends to connect blobs together. it is implemented
        as a sigma of a gausian blur in um
    fraction_in is the fraction of points from all images to include in the region
    """
    # get blured which corrisponds to closeness to a point
    sigma = tuple(connectedness / s for s in working_scale)
    blured = get_blured(sigma)
    brightesses: list[float] = []
    for _, (x, y, z) in pix_spots.iterrows():
        pix_value = blured[x, y, z]
        brightesses.append(float(pix_value))
    thresh = np.quantile(brightesses, 1-fraction_in)
    assert image.max() == 255
    neuropil_mask = image > 128
    high_mask = ((blured >= thresh) & neuropil_mask).astype(np.uint8) * 255
    viewer.add_labels(high_mask, scale=working_scale, name=f"{connectedness}-{fraction_in} in")
    nrrd.write(
        str("hb_puncta_mask.nrrd"),
        high_mask,
        compression_level=1,
        header={"spacings": working_scale},
    )
    # get equal volume min 
    fraction_in_mask = high_mask.mean() / 255
    blured_in_neuropil_brightnesses = blured[neuropil_mask]
    low_thresh = np.quantile(blured_in_neuropil_brightnesses, fraction_in_mask)
    low_mask = ((blured<=low_thresh) & neuropil_mask).astype(np.uint8) * 255
    viewer.add_labels(low_mask, scale=working_scale, name=f"{connectedness}-{fraction_in} out")
    nrrd.write(
        str("hb_puncta_anti_mask.nrrd"),
        low_mask,
        compression_level=1,
        header={"spacings": working_scale},
    )





