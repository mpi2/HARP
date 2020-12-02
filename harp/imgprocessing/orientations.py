"""
Some flips are needed on the output data so it's ready for the IMPC

All stacks should be in RAS format before submitting to the DCC

UCD and TCP have there embryos in a non-stnadard orientation, so need extra transformations
"""
import numpy as np

# For the NRRD header
SPACE = 'right-anterior-superior'

SPACE_DIRECTIONS = np.array([[1,0,0], [0,1,0], [0,0,1]])

RAS_HEADER_OPTIONS = {
        'space': SPACE,
        'space directions': SPACE_DIRECTIONS
    }


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
