from pathlib import Path
from subprocess import run

import click

template_path = Path("template.nrrd")


@click.command(
    help="reformat all images matching **/chan*.nrrd with affine-xforms dirs to the template"
)
def main():
    for xform_path in Path().glob("**/affine.xform"):
        print(xform_path)
        img_dir = xform_path.parent
        moving_paths = list(img_dir.glob(f"chan*.nrrd"))
        moving_paths.append(img_dir / "neuropil_mask.nrrd")
        for moving_path in moving_paths:
            if "reformat" in moving_path.name:
                continue

            click.echo(f"reformating on {moving_path}", err=True)
            args = (
                "reformatx",
                "-o",
                xform_path.parent / moving_path.with_suffix(".reformat.nrrd").name,
                "--floating",
                moving_path,
                template_path,
                xform_path
            )
            run(args, check=True)

main()
