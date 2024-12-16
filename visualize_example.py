"""
plot a reformated neurpil mask with all points
colored by category
"""
from __future__ import annotations
from pathlib import Path
import json
from itertools import chain
import string

import napari.utils
import pandas as pd
import nrrd
import click
import numpy as np
import napari

# directory = Path("Control-00--L0-230913_NB5-2;UAS-FLP,Brp-V5_488V5_555CadN_647FasII_647Eve_slide1L_1_A1 2")

HB_PUNCTA_COLOR = "#00FFFF"
ANTI_HB_PUNCTA_COLOR = "#FF00FF"
NUMBERED_VOLUME_COLORS  = [
    '#000000', '#000000', '#000000', '#000000'
]

N_EXAMPLE_IMAGES_TO_SHOW = 1
ONLY_LEFT = True

def get_colormap(hex_string: str) -> napari.utils.Colormap:
    hex_color = hex_string.lstrip('#')
    rgb_int = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    rgb_float = tuple(i / 255 for i in rgb_int)
    colors = np.array([(0, 0, 0), rgb_float])
    return napari.utils.Colormap(colors)

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True), default=None)
def main(paths: list[click.Path]):
    """
    plots the points and the mask colored by category
    """
    if not paths:
        paths = list(chain.from_iterable(json.loads(Path("region_defining_files.json").read_text()).values()))
        for path in paths.copy():
            paths.append(str(Path(path).parent / "fliped_puncta.csv"))
    #add all points
    viewer = napari.Viewer()
    for path in paths:
        spots = pd.read_csv(str(path), index_col=0)
        viewer.add_points(spots, size=.2, name=path)
    # add general purpose masks
    left_neuropil, _ = nrrd.read("left_neuropil.nrrd")
    if not ONLY_LEFT:
        left_neuropil[:] = True
    hb_image, metadata = nrrd.read("hb_puncta_mask.nrrd")
    hb_image *= left_neuropil
    viewer.add_image(hb_image, rendering="iso", colormap=get_colormap(HB_PUNCTA_COLOR), blending="translucent", name="hb region", scale=metadata["spacings"])
    not_hb_image, _ = nrrd.read("hb_puncta_anti_mask.nrrd")
    not_hb_image *= left_neuropil
    viewer.add_image(not_hb_image, rendering="iso", colormap=get_colormap(ANTI_HB_PUNCTA_COLOR), blending="translucent", name=" antihb region", scale=metadata["spacings"])
    template_image, _ = nrrd.read("template.nrrd")
    viewer.add_image(template_image * left_neuropil, rendering="iso", scale=metadata["spacings"], name="template")
    i = 0
    for mask_path in Path().glob("*.nrrd"):
        if mask_path.name[0] not in string.digits:
            continue
        mask, _ = nrrd.read(str(mask_path))
        viewer.add_image(mask*255, rendering="iso", colormap=get_colormap(NUMBERED_VOLUME_COLORS[i]), blending="translucent", name=mask_path.name, scale=metadata["spacings"])
        i += 1
    # image specific images
    visited_directories = []
    for i, path in enumerate(paths):
        if i >= N_EXAMPLE_IMAGES_TO_SHOW:
            break
        directory = Path(str(path)).parent
        if directory in visited_directories:
            continue
        visited_directories.append(directory)
        reformat, _ = nrrd.read(str(directory / "neuropil_mask.reformat.nrrd"))
        reformat *= left_neuropil
        viewer.add_image(reformat*255, rendering="iso", scale=metadata["spacings"], name="neuropil", blending="additive")
        reformat_voxel, _ = nrrd.read(str(directory / "chan3.reformat.nrrd"))
        viewer.add_image(reformat_voxel, scale=metadata["spacings"], name="3", blending="additive")
        reformat_voxel, _ = nrrd.read(str(directory / "chan2.reformat.nrrd"))
        viewer.add_image(reformat_voxel, scale=metadata["spacings"], name="2", blending="additive", colormap="green")
        reformat_voxel, _ = nrrd.read(str(directory / "chan1.reformat.nrrd"))
        viewer.add_image(reformat_voxel, scale=metadata["spacings"], name="1", blending="additive", colormap="magenta")
        reformat_voxel, _ = nrrd.read(str(directory / "chan0.reformat.nrrd"))
        viewer.add_image(reformat_voxel, scale=metadata["spacings"], name="0", blending="additive", colormap="cyan")
    napari.run()


main()
