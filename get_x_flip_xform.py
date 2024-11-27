"""
gets the transformation matrix that is equivalent to flipping on the x axis
"""

from pathlib import Path
import napari
from napari.layers import Points
from subprocess import run

import nrrd
import numpy as np
import xform

FLIP_XFORM = """! TYPEDSTREAM 2.4

affine_xform {
	xlate 0 0 0
	rotate 0 0 0
	scale -1 1 1
	shear 0 0 0
	center 0 0 0
}"""


def view_img(img: np.ndarray, viewer: napari.Viewer, metadata: dict, name: str):
    """
    veiws an xyz pnrrd read image in napari
    """
    scale = metadata["spacings"][::-1]
    img_zyx = img.transpose((2, 1, 0))
    viewer.add_image(img_zyx, scale=scale, name=name)


def main(view=False):
    viewer: napari.Viewer | None = None
    # make xflip template
    template_path = Path("template.nrrd")
    img, metadata = nrrd.read(str(template_path))
    if view:
        viewer = napari.Viewer()
        view_img(img, viewer, metadata, "orig_template")
        viewer.add_points(data=[[14, 5, 26]], ndim=3, name="left_lobe")
    inverted_metadata = metadata.copy()
    inverted_metadata["spacings"][0] *= -1
    # inverted_metadata["space directions"] = np.diag(inverted_metadata["spacings"])
    if viewer is not None:
        view_img(img, viewer, inverted_metadata, "xfliped")
    # del inverted_metadata["spacings"]
    inverted_path = Path("inverted_template.nrrd")
    nrrd.write(str(inverted_path), img, header=inverted_metadata)
    # make the xform
    mirror_xform_path = Path("mirror.xform")
    mirror_xform_path.write_text(FLIP_XFORM)
    translate_affine_path = Path("xlate.xform")
    args = (
        "make_initial_affine",
        "--centers-of-mass",
        template_path,
        inverted_path,
        translate_affine_path,
    )
    print(args)
    run(args, check=True)
    # then concatinate the xforms
    init_xfom_path = Path("init.xform")
    args = (
        "concat_affine",
        "--outfile",
        init_xfom_path,
        translate_affine_path,
        mirror_xform_path,
    )
    print(args)
    # map template onto itself after flipping it
    run(args, check=True)
    affine_path = Path("flip.xform")
    args = (
        "registration",
        "--initial",
        init_xfom_path,
        "--dofs",
        "6,9",
        "--auto-multi-levels",
        "4",
        "-a",
        "0.5",
        "-o",
        affine_path,
        template_path,
        template_path,
    )
    print(args)
    run(args, check=True)
    # reformat template
    flipped_template_path = Path("flipped_template.nrrd")
    args = (
        "reformatx",
        "-o",
        flipped_template_path,
        "--cubic",
        "--floating",
        template_path,
        template_path,
        init_xfom_path,
    )
    print(args)
    run(args, check=True)
    fliped_template, _ = nrrd.read(str(flipped_template_path))
    if viewer is not None:
        view_img(fliped_template, viewer, metadata, "fliped_template")
    # sum them together
    avg_template = (
        (fliped_template.astype(np.uint16) + img.astype(np.uint16)) / 2
    ).astype(np.uint8)
    if viewer is not None:
        view_img(avg_template, viewer, metadata, "fliped_template")
        this_xform = -xform.CMTKtransform(affine_path)
        points_zyx, = next(l.data for l in viewer.layers if isinstance(l, Points))
        points_xyz = points_zyx[::-1]
        out_points_xyz = this_xform.xform(np.array([points_xyz]))
        viewer.add_points(out_points_xyz[0][::-1])

    mirror_xform_path.unlink()
    translate_affine_path.unlink()
    nrrd.write(str(template_path), avg_template, header=metadata)
