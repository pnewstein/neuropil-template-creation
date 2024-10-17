#####################
# INSTALLATION
#####################

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
# Segment out the neuropil channel (if not all neuropil channels are the same.
# Just drag and drop them all in)
# NOTE: this also trys to determine if z needs to be inverted. If so, the
# script will create an inverted_neuropil_mask.nrrd file. This file can be used
# for template formation but not for affine transformation. This is because the
# puncta coordinates do not match the inverted file. Instead, the script
# generates a init.xform which flips the z axis.
conda run -n template-env python segment_neuropil.py **/chan0.nrrd

####################
# Make a template
####################
# Initialize three-image groupwise alignment using centers of mass (drag neuropil_mask from best images here)
groupwise_init -O groupwise_mask/initial -v --align-centers-of-mass  **/neuropil_mask.nrrd
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


########################
# register all images to the template
########################
conda run -n template-env python affine_register_all_images.py

##################
# reformat into template coordinates
####################
# transform puncta into template coordinates
conda run -n template-env python xform_brp_puncta.py
# re-render all images into template coordinates
conda run -n template-env python reformat_all_imgs.py

#######################
# Define regions of VNC
#######################
conda run -n template-env ipython -i define_hb_postive_regions.py
