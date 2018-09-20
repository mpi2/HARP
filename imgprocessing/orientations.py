"""
Some flips are needed on the output data so it's ready for the IMPC

All stacks should be in RAS format before submitting to the DCC

UCD and TCP have there embryos in a non-stnadard orientation, so need extra transformations
"""
import numpy as np

# For the NRRD header
SPACE = 'right-anterior-superior'

SPACE_DIRECTIONS = np.array([[1,0,0], [0,1,0], [0,0,1]])


def orient_for_impc(volume, center):
    """
    Apply appropriate transformations to volume so it can be uploaded to the IMPC
    :param volume:
    :param center:
    :return:
    """

    if center.lower() == 'tcp':
        volume = np.rot90(volume, k=3)

    elif center.lower() == 'ucd':
        volume = np.rot90(volume, k=2)

    # Do some flipping to get into RAS
    ras_volume = np.swapaxes(volume.T, 1, 2)[::-1, :, :]

    return ras_volume