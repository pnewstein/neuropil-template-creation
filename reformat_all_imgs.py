from pathlib import Path
from subprocess import run

import click

template_path = Path("template.nrrd")


@click.command(
    help="reformat all images matching **/chan*.nrrd with affine-xforms dirs to the template"
)
def main():
    for xform_path in Path().glob("**/affine.xform"):
        moving_paths = list(xform_path.parent.glob(f"chan*.nrrd"))
        for moving_path in moving_paths:
            if "reformat" in moving_path.name:
                continue
            click.echo(f"reformating on {moving_path}", err=True)
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
