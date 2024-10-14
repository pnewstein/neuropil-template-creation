from pathlib import Path
from subprocess import run

import click

template_path = Path("groupwise/affine/average.nii.gz")


@click.command(
    help="reformat all images matching **/chan*.nrrd with affine-xforms dirs to the template"
)
@click.argument(
    "template-path", type=click.Path(exists=True)
)
def main(template_path: Path):
    for xform_path in Path().glob("**/affine.xform"):
        moving_paths = list(xform_path.parent.glob(f"chan*.nrrd"))
        for moving_path in moving_paths:
            if "reformat" in moving_path.name:
                continue
            args = (
                "reformatx",
                "-o",
                moving_path.with_suffix(".reformat.nrrd"),
                "--floating",
                moving_path,
                template_path,
                xform_path
            )
            run(args, check=True)


main()
