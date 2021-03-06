Adjusting default processing parameters and variables
-----------------------------------------------------


A user may want to ajust certain variables according to its needs, the following page documents which variables of the satmo can be edited and for which purpose. All global variables are in ``satmo/global_variables.py``

Adding variables to the OC2 collection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``OC2`` is a non standard L2 suite produced by the near real time component of the system. By default this collection includes the Raileyght corrected reflectances (``rhos_nnn``) to which are later on then appended fai and afai. To enable other variables to be generated by seadas l2gen, you must append these products to the global variable ``VARS_FROM_L2_SUITE`` located in ``satmo.global_variables``.

Product that seadas l2gen is not able to generate can also be added to the ``OC2`` collection by adding them to the ``BAND_MATH_FUNCTIONS`` global variables. The inputs required by the function listed in the ``BAND_MATH_FUNCTIONS`` must be available in the initial ``OC2`` L2 file.

If you wish to produce L3m data from these new variables, you'll likely need to edits the ``STANDARD_L3_SUITES`` and ``L2_L3_SUITES_CORRESPONDENCES``, eventually creating a new L3 suite for that/these variable(s).


Change default masking parameters used for spatial binning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Seadas l2bin, called in the ``timerange_bin_map.py`` command line, uses a set of masking parameters that differs for each L3 suite. These masking parameters are stored in the ``FLAGS`` global variable and can therefore be edited from there.

Note that the ``timerange_bin_map.py`` command line also includes a --flag argument that overrides the default flags values retrieved from the ``FLAGS`` global variable.


Data visualization
^^^^^^^^^^^^^^^^^^

The ``make_preview.py`` command line that allows png previews to be generated relies for its scaling and color ramp selection on a global variable named ``VIZ_PARAMS``. The selection of parameters is based on the variable name and specific to each variable. New variables should therefore be added as entry to that global variable. 



Using the system in a different region of the world
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Nearly all the functions of the library are generic and can be applied to ocean color data all around the world. There is one exception; the ``is_day()`` function from the ``utils`` module is tailored to the Mexico zone. Users that wish to use satmo in different regions should therefore adjust the threshold values of that function.

Additionally, the near real time mode uses `data subscriptions`_ to retrieve the most recent real time and refined processing ocean color data. These subscriptions are obviously tailored to the initial satmo area, and new subscriptions should be made for the system to be operational in another part of the world. In satmo, data subscriptions codes are stored in the global variable ``SUBSCRIPTIONS``. 

.. _data subscriptions: https://oceandata.sci.gsfc.nasa.gov/subscriptions/