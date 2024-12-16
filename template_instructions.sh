##############
# Installation
##############

# - Download CMTK from https://www.nitrc.org/projects/cmtk
# - Add binary directory to path
# https://techpp.com/2021/09/08/set-path-variable-in-macos-guide/ on my
# machine, the binary directory is at /opt/local/lib/cmtk/bin/
# - install anaconda
conda env create -yf environment.yml

###############################
# pre-process all of the images
###############################
# move all
# Convert images to nrrds using a python script
conda run -n template-env python read_imaris.py *.ims
# get a list off all of the neuropils
conda run -n template-env python neuropil.py
# Segment out the neuropil channel (if not all neuropil channels are the same.
# Just drag and drop them all in)
# NOTE: this also tries to determine if z needs to be inverted. If so, the
# script will create an inverted_neuropil_mask.nrrd file. This file can be used
# for template formation but not for affine transformation. This is because the
# puncta coordinates do not match the inverted file. Instead, the script
# generates a init.xform which flips the z axis.
conda run -n template-env python segment_neuropil.py all_neuropils.json

#################
# Make a template
#################
# first find all of the images you want to use in the template and write their file indices in good_index.txt
conda run -n template-env python prepare_neuropil_for_template.py good_index.txt
# Initialize three-image groupwise alignment using centers of mass (drag neuropil_mask from best images here)
groupwise_init -O groupwise_mask/initial -v --align-centers-of-mass  **/for_template.nrrd
gunzip -f groupwise_mask/initial/groupwise.xforms.gz

# Affine groupwise registration with zero-sum transformation parameters
# over all images. Use 20% stochastic sampling density for speed.
# Use ‘‘RMI’’-based similarity measure; sometimes more robust for affine.
groupwise_affine --rmi -O groupwise_mask/affine -v --match-histograms \
--dofs 6 --dofs 9 --zero-sum \
--downsample-from 8 --downsample-to 1 --exploration 8 -a 0.5 \
--sampling-density 0.05 --force-background 0 --output-average template.nrrd \
groupwise_mask/initial/groupwise.xforms
gunzip -f groupwise_mask/affine/groupwise.xforms.gz
conda run -n template-env python post_proc_template.py
# also calculate the transformation matrix from left to right neuropil
conda run -n template-env python get_x_flip_xform.py



#####################################
# Register all images to the template
#####################################
# first find all of the upside down neuropils. Using the `view` function from
# prepare_neuropil_for_template may help put these indices into flipz.txt
# then do the flipping
conda run -n template-env python flip_ax.py flipz.txt
conda run -n template-env python affine_register_all_images.py

####################################
# Reformat into template coordinates
####################################
# re-render all images into template coordinates
conda run -n template-env python reformat_all_imgs.py
# check the quality of the transformation
conda run -n template-env python evaluate_xform.py

##########################
# Find puncta using imaris
##########################
# export high quality images
conda run -n template-env python export_reformated_images.py
# then use imaris spots feature to find synapse puncta
# import puncta from imaris
conda run -n template-env python import_imaris_spots.py imports/*.ims


#######################
# Define regions of VNC
#######################
# figure out which files to use for neuropil definitions 
conda run -n template-env python neuropil.py --puncta

# NOTE: this step requires a gui.
conda run -n template-env ipython -i define_hb_postive_regions.py region_defining_files.json
# then run make-regions in the python interpereter:  make_regions(connectedness: float, fraction_in: float):
    #make_regions defines a region what includes fraction_in of the points
    #it adds a new layer to the napari viewer and saves a nrrd

    #increasing connectedness tends to connect blobs together. it is implemented
        #as a sigma of a gausian blur in um
    #fraction_in is the fraction of points from all images to include in the region
# blured = make_regions(connectedness= 1, fraction_in=.95)
    # next create a new points layer. Then select a seed for all of the split neuropils you would like to create
    # then run the following code
# split_regions(blured)


###################
# Quantify all data
###################
# Runs on all of the reformated_puncta files creates quantification.csv
# see documention of main function for column names and descriptions
conda run -n template-env python make_spreadsheet.py region_defining_files.json
