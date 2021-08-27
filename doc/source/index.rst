.. toctree::
   :hidden:
   :maxdepth: 2

   Home <self>
   datasets
   tools
   troubleshooting
   changelog


Introduction
============

``connectome-tools`` package is a collection of tools for specifying and analysing circuit connectivity.

It relies on `BluePy <https://bbpteam.epfl.ch/documentation/projects/bluepy/latest/>`_ for accessing circuit data.

At the moment these tools are provided:

**connectome-stats**
    Sampling some connectome statistics from the circuit.

**s2f-recipe**
    Writing synapse pruning recipe used by `Functionalizer <https://bbpteam.epfl.ch/documentation/projects/functionalizer/latest/>`_ / `Spykfunc <https://bbpteam.epfl.ch/documentation/projects/spykfunc/latest/index.html>`_

**s2f-recipe-merge**
    Wrapping and executing ``s2f-recipe`` for different regions, merging the results into a single recipe.


Installation
============

module load
-----------

The easiest way to get ``connectome-tools`` package might be with a Spack *module*:

.. code-block:: console

    $ module load unstable connectome-tools


To ensure the result obtained with the tools is reproducible, please consider using some specific `BBP archive S/W release <https://bbpteam.epfl.ch/project/spaces/display/BBPHPC/BBP+ARCHIVE+SOFTWARE+MODULES>`_.

pip install
-----------

Alternatively, ``connectome-tools`` is also distributed as a Python package available at BBP devpi server:

.. code-block:: console

    $ pip install -i https://bbpteam.epfl.ch/repository/devpi/simple/ connectome-tools

Only Python 3.8+ is supported at the moment.


Acknowledgments
===============

``connectome-tools`` is a refactored subset of ``bluerecipe`` toolset originally developed by `Michael Reimann <mailto:michael.reimann@epfl.ch>`_.


Reporting issues
================

``connectome-tools`` is maintained by BlueBrain NSE team at the moment.

Should you face any issue with using it, please submit a ticket to our `issue tracker <https://bbpteam.epfl.ch/project/issues/browse/NSETM>`_; or drop us an `email <mailto: bbp-ou-nse@groupes.epfl.ch>`_.

