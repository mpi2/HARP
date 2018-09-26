"""
Some flips are needed on the output data so it's ready for the IMPC

All stacks should be in RAS format before submitting to the DCC

UCD and TCP have there embryos in a non-stnadard orientation, so need extra transformations
"""
import numpy as np

# For the NRRD header
SPACE = 'right-anterior-superior'

SPACE_DIRECTIONS = np.array([[1,0,0], [0,1,0], [0,0,1]])


def orient_for_impc(volume):
    """
    Apply appropriate transformations to volume so it can be uploaded to the IMPC
    Apply to the whole volume. Can be used on scaled stacks that don't take up the whole memory
    :param volume:
    :param center:
    :return:
    """
    # Do some flipping to get into RAS
    ras_volume = np.swapaxes(volume.T, 1, 2)[::-1, :, :]

    return ras_volume


def orient_slice_for_impc(img_slice, center, i):
    """
    Apply appropriate transformations to volume so it can be uploaded to the IMPC
    Apply to the whole volume. Can be used on scaled stacks that don't take up the whole memory
    """
    from skimage.io import imshow
    import matplotlib.pyplot as plt
    t = False
    # if i%30 == 0:
    #     t = True

    if t:
        imshow(img_slice)
        plt.show()
    print(center)
    if center.lower() == 'tcp':
        img_slice = np.rot90(img_slice, k=3)

    elif center.lower() == 'ucd':
        img_slice = np.rot90(img_slice, k=2)
        img_slice = np.fliplr(img_slice)

    if t:
        imshow(img_slice)
        plt.show()

    img_slice = np.flipud(img_slice)
    if t:
        imshow(img_slice)
        plt.show()

    return img_slice