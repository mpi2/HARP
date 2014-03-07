#!/usr/bin/python

import sys
import zproject


img_dir = sys.argv[1]

zp = zproject.Zproject(img_dir)
zp.run()