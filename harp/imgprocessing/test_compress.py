"""
230518

Having problems with bzp_nrrd.

Run some tests
"""


from . import compress
import os

test_nrrd = '/home/neil/mousedata/MicroCT/project-IMPC_MCT/processed_recons/20180419_LDB3_E14.5_9.5h_HOM_XY_REC/scaled_stacks/20180419_LDB3_E14.5_9.5h_HOM_XY_REC_scaled_4.7297_pixel_13.9999.nrrd'
test_outfile = '/home/neil/Desktop/t/testout'


class Update():
    def emit(self, msg):
        print(msg)


def run():
    with open(test_nrrd, 'r') as open_nrrd_file:
        compress._write_bzp2(test_outfile,  open_nrrd_file, 'test_scan', Update())


run()
