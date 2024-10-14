#####################
# INSTALATION
#####################

# Download CMTK from https://www.nitrc.org/projects/cmtk
# Add binary directory to path https://techpp.com/2021/09/08/set-path-variable-in-macos-guide/ on my machine, the binary directory is at /opt/local/lib/cmtk/bin/
# install anaconda
conda env create -yf environment.yml

###############################
# preprocess all of the images
###############################
# move all 
# Convert images to nrrds using a python script 
conda run -n template-env python read_imaris.py *.ims
# Segment out the neuropil channel (if not all neuropil channes are the same. just drag and drop them all in)
conda run -n template-env python segment_neuropil.py **/chan0.nrrd

####################
# Make a template
####################
# Initialize three-image groupwise alignment using centers of mass (drag neuropil_mask from best images here)
groupwise_init -O groupwise_mask/initial -v --align-centers-of-mass **/neuropil_mask.nrrd
gunzip groupwise_mask/initial/groupwise.xforms.gz

# Affine groupwise registration with zero-sum transformation parameters
# over all images. Use 20% stochastic sampling density for speed.
# Use ‘‘RMI’’-based similarity measure; sometimes more robust for affine.
groupwise_affine --rmi -O groupwise_mask/affine -v --match-histograms \
--dofs 6 --dofs 9 --zero-sum \
--downsample-from 8 --downsample-to 1 --exploration 8 -a 0.5 \
--sampling-density 0.05 --force-background 0 \
groupwise_mask/initial/groupwise.xforms
gunzip groupwise_mask/affine/groupwise.xforms.gz


########################
# register all images to the template
########################
conda run -n template-env python affine_register_all_images.py

##################
# reformat all channels
####################
conda run -n template-env python reformat_all_imgs.py groupwise_mask/affine/average.nii.gz
