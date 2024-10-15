from pathlib import Path
from subprocess import run


template_path = Path("template.nrrd")

def main():
    moving_paths = list(Path().glob(f"**/neuropil_mask.nrrd"))
    for moving_path in moving_paths:
        affine_path = moving_path.parent / "affine.xform"
        args = (
            "make_initial_affine",
            "--centers-of-mass",
            template_path,
            moving_path,
            "init.xform",
        )
        run(args, check=True)
        args = (
            "registration",
            "--initial",
            "init.xform",
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
        run(args, check=True)


main()
