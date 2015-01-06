#!/usr/bin/python

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


