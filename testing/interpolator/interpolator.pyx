import numpy as np
cimport numpy as np
cimport cython
import SimpleITK as sitk
import scipy.ndimage


def interpolate(img_path_list,  input_voxel_size, output_voxel_size, get_dimensions):
    """
    Unfinished. But does not produce satisfactory results as it's very very slow (5s /pixel) and uses loads of RAM
    1.2GB for 150mb  for 150MB stack
    :return:
    """
    dims = get_dimensions(img_path_list)  # !
    scale_factor = 2
    new_dimensions = tuple(x//scale_factor for x in dims)
    print new_dimensions
    print 'cython'
    raw_file = '/home/neil/work/harp_test_data/out/tempMemapDelete.raw'
    #mapped_array = np.memmap(raw_file, dtype=np.uint8, mode='r', shape=dims)
    mapped_array = np.fromfile(raw_file, dtype=np.uint8).reshape(dims)

    new_array = np.zeros(new_dimensions, dtype=np.uint8)

    z_array = np.linspace(1.0/scale_factor, dims[0] - (1.0/scale_factor), dims[0]/scale_factor)
    x_array = np.linspace(1.0/scale_factor, dims[2] - (1.0/scale_factor), dims[2]/scale_factor)
    y_array = np.linspace(1.0/scale_factor, dims[1] - (1.0/scale_factor), dims[1]/scale_factor)

    #grid = np.meshgrid(z_array, y_array, x_array, sparse=True)
    count = 0
    y_ccords = np.repeat(y_array, len(x_array))
    x_coords = np.repeat(x_array, len(y_array))

    for i, z in enumerate(z_array):

        z_coords = np.repeat(z, (x_array.size * y_array.size))

        interpolated_slice = scipy.ndimage.interpolation.map_coordinates(mapped_array, (z_coords, y_ccords, x_coords))
        #print 'new', interpolated_slice.size
        #print type(interpolated_slice)
        r = interpolated_slice.reshape(new_dimensions[1:3])

        #print interpolated_voxel
        new_array[i, :, :] = r
    img_out = sitk.GetImageFromArray(new_array)
    sitk.WriteImage(img_out, 'interolated.nrrd')
