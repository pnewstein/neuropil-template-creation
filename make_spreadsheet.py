"""
makes a csv file of puncta counts in each condition
"""

from pathlib import Path
import string
import json

import numpy as np
import pandas as pd
import nrrd
import click


from import_imaris_spots import in_mask
from evaluate_xform import reindex


@click.command()
@click.argument("json_path", type=click.Path(exists=True))
def main(json_path):
    """
    makes a csv file of puncta counts in each condition
    columns are
        Condition
            Control, hb_presynapses, HbOE
        idx
            the file number
        used for anti-hb-puncta
            whether this image was used to create the control neuropil
        in_neuropil
            The number of puncta that are in the template hemi-segment neuropil
        file_name
            the original name of the image
        count in hb-punca zone
            The number of puncta that are in the zone annotated as high in hb filtered punca
        count in anti-hb-puncta zone
            The number of puncta that are in the zone annotated as low in hb filtered punca
        count in lbl *
            the number of punta in a label for each label
        also the above three in terms of percent of in_neuropil
        score
            the quality of the alignment to the template image (higher is better)
        side
            left or right
    """
    used_control_images = [s.split("--")[0] for s in json.loads(Path(json_path).read_text())["ctrl"]]
    left_neuropil, _ = nrrd.read("left_neuropil.nrrd")
    hb_image, _ = nrrd.read("hb_puncta_mask.nrrd")
    left_hb = hb_image * left_neuropil
    not_hb_image, _ = nrrd.read("hb_puncta_anti_mask.nrrd")
    left_not_hb = not_hb_image * left_neuropil
    template_metadata = nrrd.read_header("template.nrrd")
    lbl_masks = {
        p.name[0]: nrrd.read(str(p))[0]
        for p in Path().glob("*.nrrd")
        if p.name[0] in string.digits
    }
    dfs: list[pd.DataFrame] = []
    for use_right in (True, False):
        serieses: list[pd.Series] = []
        for path in Path().glob("**/reformated_puncta.csv"):
            series_dict: dict[str, float | bool] = {}
            series_dict["used for anti-hb-puncta"] = path.parent.name.split("--")[0] in used_control_images
            if use_right:
                neuropil_spots = pd.read_csv(path.parent / "fliped_puncta.csv", index_col=0)
            else:
                neuropil_spots = pd.read_csv(path, index_col=0)
            pix_spots = np.round(neuropil_spots / template_metadata["spacings"]).astype(int)
            in_left_neuropil = in_mask(pix_spots, left_neuropil)
            series_dict["in neuropil"] = in_left_neuropil.sum()
            in_hb_image = in_mask(pix_spots, left_hb)
            series_dict["count in hb-puncta zone"] = in_hb_image.sum()
            in_not_hb_image = in_mask(pix_spots, left_not_hb)
            series_dict["count in anti-hb-puncta zone"] = in_not_hb_image.sum()
            for lbl, mask in lbl_masks.items():
                in_lbl = in_mask(pix_spots, mask)
                series_dict[f"count in lbl {lbl}"] = in_lbl.sum()
            serieses.append(
                pd.Series(
                    series_dict,
                    name=path.parent.name,
                )
            )
        df = pd.DataFrame(serieses)
        for col in df.columns:
            if not col.startswith("count"):
                continue
            new_name = "percent" + col.split("count")[-1]
            df[new_name] = 100 * df[col] / df["in neuropil"]
        df = reindex(df)
        qual = pd.read_csv("xform_qual.csv", index_col=0)
        df = df.join(qual["score"])
        dfs.append(df)
        side = "right" if use_right else "left"
        df["side"] = side
        df.index = [f"{ind}-{side}" for ind in df.index]
    df = pd.concat(dfs, axis=0)
    df.to_csv("quantification.csv")



if __name__ == "__main__":
    main()
