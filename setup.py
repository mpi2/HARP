# coding: utf-8
# PyQt Notes
# Cannot get PyQt5>=5.14.2 on fedora 5.6.15-200.fc31.x86_64 installed
# Ubuntu 20.04  5.15.2 was causing issues so used 5.14.2





from setuptools import setup, find_packages

setup(
    name='harp_image_preprocess',
    version='2.4.1.0',
    packages=find_packages(exclude=("dev")),
    include_package_data=True,
    install_requires=[
	"numpy>=1.19.0",
	"logzero>=1.5.0",
	"matplotlib>=3.3.0",
	"scikit_image>=0.17.2",
	"opencv_python",
	"Image>=1.5.33",
	"Pillow>=8.0.1",
	"PyQt5==5.14.2", # had problems with 5.15.2
	"PyYAML>=5.3.1",
	"SimpleITK>=1.2.0",
	"strconv>=0.4.2",
	"pynrrd",
	"appdirs",
	"tifffile"
    ],

    url='https://github.com/mpi2/HARP',
    license='Apache2',
    author='Neil Horner',
    author_email='n.horner@har.mrc.ac.uk, bit@har.mrc.ac.uk',
    description='Cross-platform application for automating the processing of μCT and OPT image data.',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
     ],
    keywords=['image processing', 'micro-CT'],
    entry_points ={
            'console_scripts': [
                'harp_run=harp.run_harp:main',
                'harp_batch=harp.batch:main'
            ]
        },
)
