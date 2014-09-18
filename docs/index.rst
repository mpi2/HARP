

.. HARP documentation master file, created by
   sphinx-quickstart on Mon Sep 15 14:57:52 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to HARP's documentation!
================================

HARP v1.0.1: Harwell Automated Recon Processor

Tool to crop, scale and compress reconstructed images from microCT  or OPT data

Allows the user to setup a parameter file in the first tab. This is saved and added to a processing list. Multiple
parameter files can be generated and added to the list. The list can then be processed and the status checked
by looking at the processing tab.


Content
==================


Parameter creating modules
------------------

Modules used to get the parameter file and for GUI interactions.

The Module **harp** is the main module for the tool.

.. toctree::
    :glob:

    harp
    autofill
    errorcheck
    getpickle
    addtolist
    config
    getdimensions


Processing modules
------------------

Modules used to perform the actual processing

.. toctree::
    :glob:

    processing
    autocrop
    zproject
    crop


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. autoclass:: my.Class
   :members:
   :private-members:
   :special-members:
