.. satmo documentation master file, created by
   sphinx-quickstart on Wed Apr  5 12:37:42 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

satmo (Sistema Satelital de Monitoreo Oceanico)
===============================================

This is the documentation of the ``satmo`` python package. The source code is available in a
git repository hosted at https://github.com/CONABIO/satmo

Image of a preview.


Introduction
============



User guide
==========

.. toctree::
   :maxdepth: 2

   cli

Operating the system.
   Starting the virtual environment (created in the installation instructions)

   A set of command lines is used to operate the system (prefix timerange, documentation can be accessed by running command.py --help)

   NRT mode -- mostly in the cron but can also be started 
   Processing mode (for each command, mention what should have been ran before, and give a print of the help page)
      Downloading data
      Running atmospheric correction (l2gen)
      Generating additional variables
      Mapping swath data
      Generating composites (bin-map)
      Temporal compositing
      Generate previews (show some examples)

   In technical documentation section, present a flow chart for the main command lines

   Example script to go from download to L3m

Adding new variables or collections
   Many processing parameters (default masking values, formulas, suites, variables) are stored in global variables, stored in satmo/oceancolor/global_variables.py. The section below explains which variables have to be edited ...




Technical documentation
=======================

.. toctree::
   :maxdepth: 2

   api/index
   conventions
   chains

Installation and documentation
==============================

.. toctree::
   :maxdepth: 2

   install
   autodoc


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
