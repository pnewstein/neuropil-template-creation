from pathlib import Path
from subprocess import run


template_path = Path("template.nrrd")

FLIP_XFORM = """! TYPEDSTREAM 2.4

affine_xform {
	xlate 0 0 0
	rotate 0 0 0
	scale 1 1 -1
	shear 0 0 0
	center 0 0 0
}"""


def main():
    moving_paths = sorted(list(Path().glob(f"**/neuropil_mask.nrrd")))
    for moving_path in moving_paths:
        init_xfom_path = moving_path.parent / "init.xform"
        inverted_mask_path = moving_path.parent / "inverted_neuropil_mask.nrrd"
        if inverted_mask_path.exists():
            # first see how you would translate fliped image
            flip_xform_path = moving_path.parent / "flip.xform"
            flip_xform_path.write_text(FLIP_XFORM)
            translate_affine_path = moving_path.parent / "xlate.xform"
            args = (
                "make_initial_affine",
                "--centers-of-mass",
                template_path,
                inverted_mask_path,
                translate_affine_path,
            )
            print(args)
            run(args, check=True)
            # then concatinate the xforms
            args = (
                "concat_affine",
                "--outfile",
                init_xfom_path,
                translate_affine_path,
                flip_xform_path,
            )
            print(args)
            run(args, check=True)

        affine_path = moving_path.parent / "affine.xform"
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
            moving_path,
        )
        print(args)
        run(args, check=True)

main()
