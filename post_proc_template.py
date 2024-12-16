"""
makes the template be uint8
"""

import nrrd
import numpy as np


def main():
    image, metadata = nrrd.read("groupwise_mask/affine/template.nrrd")
    scale = np.diag(metadata["space directions"])
    image[image == np.inf] = 0
    image = image * 254 / image.max()
    assert image.max() < 255
    out = image.astype(np.uint8)
    image_mask = out>0
    buffer_coef = .5
    bbox: list[slice] = []
    for i, length in enumerate(image.shape):
        all_axs = [0, 1, 2]
        all_axs.pop(i)
        other_axs = tuple(all_axs)
        img_1d = image_mask.sum(axis=other_axs).astype(bool)
        inds, = np.where(img_1d)
        img_ends = inds[[0, -1]]
        irange = img_ends[1] - img_ends[0]
        buffer = irange * buffer_coef
        bbox_ends = img_ends[0] - buffer, img_ends[1] + buffer
        cliped_bbox_ends = np.clip(bbox_ends, 0, length)
        bbox.append(slice(*cliped_bbox_ends.astype(int)))
    bbox0, bbox1, bbox2 = bbox
    cropped = image[bbox0, bbox1, bbox2]
    nrrd.write("template.nrrd", cropped, compression_level=1, header={"spacings": scale})


if __name__ == "__main__":
    main()
