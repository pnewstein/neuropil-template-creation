from pathlib import Path
from subprocess import run

import click


@click.command(
    help="register all images matching **/chan{chan_to_register}.nrrd to the template"
)
@click.argument("template-path", type=click.Path(exists=True))
@click.argument("chan_to_register", type=int)
def main(template_path: Path, chan_to_register: int):
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
