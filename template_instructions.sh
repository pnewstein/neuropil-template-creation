#####################
# INSTALATION
#####################

# Download CMTK from https://www.nitrc.org/projects/cmtk
# Add binary directory to path https://techpp.com/2021/09/08/set-path-variable-in-macos-guide/ on my machine, the binary directory is at /opt/local/lib/cmtk/bin/
# install anaconda
conda env create -f environment.yml

####################
# Make a template
####################
# perhaps only include your best images for speed
# First convert images to nrrds using a python script (can also be done in fiji probably)
conda run -n template-env python tif_to_nrrds.py *.tif
# Initialize three-image groupwise alignment using centers of mass
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

groupwise_warp --congeal -O groupwise_mask/warp -v --match-histograms --histogram-bins 32 \
--grid-spacing 40 --grid-spacing-fit --refine-grid 5 --zero-sum-no-affine \
--downsample-from 8 --downsample-to 1 --exploration 6.4 --accuracy 1 \
--force-background 0 groupwise_mask/affine/groupwise.xforms

########################
# register all images to the template
########################
conda run -n template-env python affine_register_all_chans.py groupwise_mask/affine/average.nii.gz 0

##################
# reformat all channels
####################
conda run -n template-env python reformat_all_imgs.py groupwise_mask/affine/average.nii.gz



# Initialize three-image groupwise alignment using centers of mass
groupwise_init -O groupwise_small/initial -v --align-centers-of-mass **/02neuropil_mask.nrrd
gunzip groupwise_small/initial/groupwise.xforms.gz

# Affine groupwise registration with zero-sum transformation parameters
# over all images. Use 20% stochastic sampling density for speed.
# Use ‘‘RMI’’-based similarity measure; sometimes more robust for affine.
groupwise_affine --rmi -O groupwise_small/affine -v --match-histograms \
--dofs 6 --dofs 9 --zero-sum \
--downsample-from 8 --downsample-to 1 --exploration 8 -a 0.5 \
--sampling-density 0.05 --force-background 0 --output-average template.nrrd \ 
groupwise_small/initial/groupwise.xforms
gunzip groupwise_small/affine/groupwise.xforms.gz

groupwise_warp --congeal -O groupwise_small/warp -v --match-histograms --histogram-bins 32 \
--grid-spacing 40 --grid-spacing-fit --refine-grid 5 --zero-sum-no-affine \
--downsample-from 8 --downsample-to 1 --exploration 6.4 --accuracy 1 \
--force-background 0 groupwise_small/affine/groupwise.xforms

########################
# register all images to the template
########################
conda run -n template-env python affine_register_all_chans.py groupwise_small/affine/average.nii.gz 0

##################
# reformat all channels
####################
conda run -n template-env python reformat_all_imgs.py groupwise_small/affine/average.nii.gz
