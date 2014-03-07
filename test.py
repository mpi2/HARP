#!/usr/bin/python

import crop
import sys


image = sys.argv[1]

def callback(box):
    print box

crop.run(callback, image)