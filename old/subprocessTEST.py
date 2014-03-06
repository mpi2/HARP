#!/usr/bin/python
import sys
import subprocess


# Running command line on windows Note shell=true is not good for security
subprocess.call('dir', shell=True)
subprocess.call(["java", "-jar", "C:\Program Files\ImageJ\ij.jar", "-batch", "\Users\t.lawson\Desktop\siah_scale.ijm", "C:\Users\t.lawson\Desktop\\test_scale\~0.5"])
