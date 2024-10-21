Introduction
============

``connectome-tools`` package is a collection of tools for specifying and analysing circuit connectivity.

At the moment these tools are provided:

**connectome-stats**
    Sampling some connectome statistics from the circuit.

**s2f-recipe**
    Writing synapse pruning recipe used by `Functionalizer <https://github.com/BlueBrain/functionalizer>`_

**s2f-recipe-merge**
    Wrapping and executing ``s2f-recipe`` for different regions, merging the results into a single recipe.


Installation
============

pip install
-----------

Note the; package depends on  `Equation <https://pypi.org/project/Equation/>`_, however this must be installed manually since one should examine the license.

``connectome-tools`` is also distributed as a Python package:

.. code-block:: console

    $ git clone https://github.com/BlueBrain/connectome-tools
    $ pip install "equation>=1.2"
    $ pip install -e connectome-tools


Acknowledgements
================

The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology.

For license see LICENSE.txt.

``connectome-tools`` is a refactored subset of ``bluerecipe`` toolset originally developed by `Michael Reimann <mailto:michael.reimann@epfl.ch>`_.

Copyright (c) 2013-2024 Blue Brain Project/EPFL
