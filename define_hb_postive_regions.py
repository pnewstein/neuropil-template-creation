from pathlib import Path
import json
from functools import lru_cache
import sys

import napari
import nrrd
import pandas as pd
import numpy as np
import scipy.ndimage as ndi
from skimage.segmentation import watershed


DOWNSCALE_FACTOR = 1


def init():
    image, metadata = nrrd.read("template.nrrd")
    viewer = napari.Viewer()
    scale = metadata["spacings"]
    viewer.add_image(image, scale=scale, name="template")
    left_neuropil, _ = nrrd.read("left_neuropil.nrrd")
    viewer.add_labels(left_neuropil, scale=scale)
    working_scale = [s * DOWNSCALE_FACTOR for s in scale]
    assert image.max() == 254
    neuropil_mask = image > 128
    paths_dict = json.loads(Path(sys.argv[-1]).read_text())
    pix_count_volumes: dict[str, np.ndarray] = {}
    for key, paths in paths_dict.items():
        orig_dfs: list[pd.DataFrame] = []
        flipped_dfs: list[pd.DataFrame] = []
        for path_str in paths:
            path = Path(path_str)
            spots = pd.read_csv(path, index_col=0)
            orig_dfs.append(spots)
            flipped_path = path.parent / "fliped_puncta.csv"
            flipped_spots = pd.read_csv(flipped_path, index_col=0)
            flipped_dfs.append(flipped_spots)
            viewer.add_points(pd.concat([spots, flipped_spots], axis=0), name=path.parent.name, size=.5, face_color="magenta")
        orig_spots = pd.concat(orig_dfs)
        flipped_spotss = pd.concat(flipped_dfs)
        all_spots = pd.concat((orig_spots, flipped_spotss), axis=0)

        pix_spots = (all_spots / working_scale).round().astype(int)
        assert isinstance(pix_spots, pd.DataFrame)
        pix_count_volume = np.zeros(
            tuple(s // DOWNSCALE_FACTOR for s in image.shape)
        ).astype(np.uint8)
        for _, (x, y, z) in pix_spots.iterrows():
            pix_count_volume[x, y, z] += 1
        max_pix_count = pix_count_volume.max()
        assert max_pix_count < 100, "maybe overflow happend"
        pix_count_volumes[key] = pix_count_volume

    @lru_cache
    def get_blured(sigma, key: str):
        return ndi.gaussian_filter(pix_count_volumes[key].astype(float), sigma)

    def make_regions(connectedness: float, fraction_in: float, hb_avoid_coef=10) -> np.ndarray:
        """
        this function defines a region what includes fraction_in of the points
        it adds a new layer to the napari viewer and saves a nrrd

        increasing connectedness tends to connect blobs together. it is implemented
            as a sigma of a gausian blur in um
        fraction_in is the fraction of points from all images to include in the region
        hb_avoid_coef is what the blured hb+ puncta image is multiplied by
        before subtracting from ctrl puncta to define the anti-hb-puncta
        """
        # get blured which corrisponds to closeness to a point
        sigma = tuple(connectedness / s for s in working_scale)
        blured = get_blured(sigma, "hb_only")
        brightesses: list[float] = []
        for _, (x, y, z) in pix_spots.iterrows():
            pix_value = blured[x, y, z]
            brightesses.append(float(pix_value))
        thresh = np.quantile(brightesses, 1 - fraction_in)
        high_mask = ((blured >= thresh) & neuropil_mask).astype(np.uint8) * 255
        viewer.add_labels(
            high_mask, scale=working_scale, name=f"{connectedness}-{fraction_in} in"
        )
        nrrd.write(
            str("hb_puncta_mask.nrrd"),
            high_mask,
            compression_level=1,
            header={"spacings": working_scale},
        )
        ctrl_blured = get_blured(sigma, "ctrl")
        ctrl_not_hb = (ctrl_blured / len(paths_dict["ctrl"])) - (
            hb_avoid_coef * blured / len(paths_dict["hb_only"])
        )
        # get equal volume min
        fraction_in_mask = (high_mask[neuropil_mask]).astype(bool).mean()
        ctrl_not_hb_in_neuropil_brightnesses = ctrl_not_hb[neuropil_mask]
        ctrl_thresh = np.quantile(
            ctrl_not_hb_in_neuropil_brightnesses, 1 - fraction_in_mask
        )
        low_mask = ((ctrl_not_hb >= ctrl_thresh) & neuropil_mask).astype(np.uint8) * 255
        viewer.add_labels(
            low_mask, scale=working_scale, name=f"{connectedness}-{fraction_in} out"
        )
        nrrd.write(
            "hb_puncta_anti_mask.nrrd",
            low_mask,
            compression_level=1,
            header={"spacings": working_scale},
        )
        return blured
    
    def split_regions():
        """
        splits up the in mask (assumed to be in the viewer layers)
        according to a watershed based on blured hb puncta (blured)
        and seeds (assemed to be the last layer). saves all watersheds as f"{lbl}.nrrd"
        """
        in_mask = next(l.data for l in viewer.layers if " in" in l.name)
        seeds_layer = viewer.layers[-1]
        assert np.allclose(seeds_layer.scale, working_scale)
        seeds = (seeds_layer.data).round().astype(int)
        markers = np.zeros(in_mask.shape, dtype=np.uint8)
        lbl_names = np.arange(len(seeds)) + 1
        markers[seeds[:, 0], seeds[:, 1], seeds[:, 2]] = lbl_names
        distance = ndi.distance_transform_edt(in_mask)
        lbls = watershed(-distance, markers, mask=in_mask)
        for lbl in lbl_names:
             if str(lbl) in viewer.layers:
                  print(lbl)
                  lbl_define_mask = viewer.layers[str(lbl)].data
                  lbls[lbls.astype(bool) & lbl_define_mask.astype(bool)] = lbl
        viewer.add_labels(lbls, scale=working_scale)
        for lbl in lbl_names:
                    nrrd.write(
            f"{lbl}.nrrd",
            (lbls==lbl).astype(np.uint8),
            compression_level=1,
            header={"spacings": working_scale},
        )
    return make_regions, split_regions



make_regions, split_regions = init()
