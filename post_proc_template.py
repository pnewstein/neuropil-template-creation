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
    nrrd.write("template.nrrd", out, compression_level=1, header={"spacings": scale})

if __name__ == "__main__":
    main()
