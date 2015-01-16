#!/usr/bin/python
"""
Copyright 2015 Medical Research Council Harwell.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

print "=== Harwell Automatic Reconstruction Processor (HARP) ===\n"
print "Downloading dependencies..."

# easy_install first
try:
    from setuptools.command import easy_install
    dependencies = ["SimpleITK", "numpy"]

    for dep in dependencies:

        try:
            print "Installing {0}...".format(dep),
            mod = __import__(dep)  # try to import module
            print " already installed.".format(dep)

        except ImportError:
            # If it fails, try to easy install it
            easy_install.main(["--user", dep])
            print "done."

except ImportError:
    print "Couldn't locate 'easy_install'."


