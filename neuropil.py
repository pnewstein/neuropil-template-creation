"""
get all of the neuropil channels
"""

from pathlib import Path
import json

import numpy as np
import click


def get_neuropil_img(directory: Path) -> Path:
    """
    returns the path to the neuropil image
    """
    if directory.name.startswith("Hb_presynapses"):
        path = directory / "chan0.nrrd"
    else:
        path = directory / "chan3.nrrd"
    return path


def get_data_dirs() -> list[Path]:
    """
    returns all of the data directories
    """
    return [
        p
        for p in Path().iterdir()
        if p.is_dir()
        and not (
            p.name.startswith(".")
            or p.name.startswith("__")
            or p.name == "groupwise_mask"
            or p.name == "flip.xform"
        )
    ]


def get_all_neuropils():
    directories = [p for p in Path().iterdir() if p.is_dir()]
    print(directories)
    paths: list[Path] = []
    for directory in directories:
        if directory.name.startswith("."):
            continue
        path = get_neuropil_img(directory)
        paths.append(str(path))
    Path("all_neuropils.json").write_text(json.dumps(paths))


def neuropil_defining_puncta():
    rng = np.random.default_rng(100)
    out_dict: dict[str, list[str]] = {"ctrl": [], "hb_only": []}
    for path in Path().glob("**/reformated_puncta.csv"):
        folder = path.parent
        if folder.name.startswith("Control"):
            out_dict["ctrl"].append(str(path))
        if folder.name.startswith("Hb_presynapses"):
            out_dict["hb_only"].append(str(path))
    out_dict["ctrl"] = list(rng.choice(out_dict["ctrl"], size=2, replace=False))
    Path("region_defining_files.json").write_text(json.dumps(out_dict, indent=2))


@click.command()
@click.option("--neuropils/--puncta", default=True)
def main(neuropils):
    if neuropils:
        get_all_neuropils()
    else:
        neuropil_defining_puncta()


if __name__ == "__main__":
    main()
