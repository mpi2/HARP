import os
from imgprocessing.io import imread
from lib import nrrd
import bz2
import tarfile


def bz2_nnrd(img_list, outfile, scan_name, update):
    """
    Create a tiff stack a directory containing single 2D images
    :param in_dir, str, directory where single images are
    :param outfile, str, path to output tiff stack
    :return:
    """

    first_image = imread(img_list[0])
    shape = list(first_image.shape)
    shape = [shape[1], shape[0]]
    shape.append(len(img_list))

    nrrd_filehandle = nrrd.get_nrrd_filehandle(outfile, shape, first_image.dtype, 3)
    compressor = bz2.BZ2Compressor()

    for i, f in enumerate(img_list):
        if i % 20 == 0:
            done = int((50.0 / len(img_list)) * i)
            update.emit('{} {}%'.format(scan_name, done))
        img_arr = imread(f)
        rawdata = img_arr.T.tostring(order='F')
        nrrd_filehandle.write(rawdata)

    nrrd_filehandle.close()

    BLOCK_SIZE = 52428800 # Around 20 MB in memory at one time
    # TODO: Check its smaller than image size
    compressed_name = outfile + '.bz2'

    file_size = os.path.getsize(outfile)
    bytes_read = 0

    with open(compressed_name, 'wb') as fh_w, open(outfile, 'rb') as fh_r:
        while True:
            block = fh_r.read(BLOCK_SIZE)
            bytes_read += BLOCK_SIZE
            done = int(50 + (50.0 / file_size) * bytes_read)
            if done >= 100: # The getsize might not be accurate?
                done = 99
            update.emit('{} {}%'.format(scan_name, done))

            if not block:
                break
            compressed = compressor.compress(block)
            if compressed:
                fh_w.write(compressed)

        # Send any data being buffered by the compressor
        remaining = compressor.flush()
        while remaining:
            to_send = remaining[:BLOCK_SIZE]
            remaining = remaining[BLOCK_SIZE:]

            fh_w.write(to_send)

    if os.path.isfile(outfile):
        try:
            os.remove(outfile)
        except OSError as e:
            update.emit("Can't delete temp file {}".format(outfile))


def bz2_dir(dir_, outfile, update, update_name, terminate):

    tar = tarfile.open(outfile + '.tar.bz2', mode='w:bz2')
    file_names = os.listdir(dir_)
    toadd = [os.path.join(dir_, x) for x in file_names]

    for i, (file_, name) in enumerate(zip(toadd, file_names)):
        if i % 5 == 0:
            if terminate.value == 1:
                return
            done = int((100.0 / len(toadd)) * i)
            update.emit("{} compression: {}%".format(update_name, done))

        tar.add(file_, arcname=name)
    tar.close()


