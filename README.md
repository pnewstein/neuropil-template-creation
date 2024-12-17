# Neuropil template creation

This code contains many python utilities and a shell script to register images
of neuropil to create a common coordinate system. Steps are detailed in
comments on the `template_instructions.sh` file, but are also summarized below:


## Installation
Install CMTK and anaconda on your own. Use the `environment.yml` to help to
create the necisary python environment

## Pre-process all of the images
Takes the imaris files, and pulls out the voxel data into an organized
directory structure, then uses the logic of `neuropil.get_neuropil_img` to
process all of the neurpil channels. The skimage code used to segment neuropil
can be found in `segment_neuropil.make_neuropil_mask`

## Make a template
The user manualy picks the files to use for the template, writing their numbers
to `good_index.txt`, then CMTK is used to perform a group wise affine
registration to create a template image based on segmented neuropils.

## Register all images to the template
first make sure none of the images have flipped Zs (due to being acquired up side
down). If there are some, put the numbers into flipz.txt and run `flip_ax.py`.
Then run `affine_register_all_images.py` to invoke CMTK to register images

## Reformat into template coordinates
Runs CMTK through `reformat_all_imgs.py` and also evaluates the quality of the
alignment with `evaluate_xform.py`.

## Find puncta using imaris
Synapse puncta are annotated using imaris, then imported using
`import_imaris_spots.py`

## Define regions of VNC
Running `define_hb_postive_regions.py` interactively can be used to define the
regions where there are many hb+ puncta. Subregions can be defined, and also
regions where there are few hb+ puncta, but many puncta in control. See the
documentation for `define_hb_postive_regions.make_regions` and
`define_hb_postive_regions.split_regions` for more information.

## Quantify all data
create a spreadsheet `quantification.csv` that quantifies each hemisegment. see
documentation for `make_spreadsheet.main` for description of columns
