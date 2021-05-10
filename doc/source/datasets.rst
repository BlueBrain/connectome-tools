Datasets
========

``connectome-tools`` utilities are built around *datasets* with connectome statistics, represented as text tabular files (tab-separated). At the moment there are two of those: bouton density per mtype (`bouton-density`), and synapse count per connection per pathway (`nsyn-per-connection`).

.. _ref-dataset-bouton-density:

bouton-density
--------------

Stores bouton density samples per mtype, along with mean / std / size for each sample.

`sample` column stores comma-separated sample values. It could be set to ``N/A``, if actual sample values are not available or not of interest.

::

    mtype   mean    std     size    sample
    *       0.383   0.198   5       N/A
    SLM_PPA 1.03    0.0523  4       0.964,0.994,1.05,1.1
    SO_BP   1.35    0       1       1.35
    SO_BS   1.44    0.0724  5       1.36,1.4,1.42,1.44,1.57

Row with mtype ``*`` corresponds to bouton density sampled regardless of mtype.

This file is readily readable with `Pandas <https://pandas.pydata.org/>`_:

.. code:: python

    import pandas as pd
    data = pd.read_csv(filepath, sep=r"\s+")

Alternatively, one can use a helper method from ``connectome_tools`` package itself:

.. code:: python

    from connectome_tools.dataset import read_bouton_density
    data = read_bouton_density(filepath, mtypes=<list of mtypes to consider>)


.. _ref-dataset-nsyn-per-connection:

nsyn-per-connection
-------------------

Stores synapse count per connection sample per pathway, along with mean / std / size for each sample.

`sample` column stores comma-separated sample values. It could be set to ``N/A``, if actual sample values are not available or not of interest.
::

    from    to      mean    std     size    sample
    SLM_PPA SLM_PPA 16.2    8.77    5       1,16,16,20,28
    SLM_PPA SO_BP   N/A     N/A     N/A     N/A
    SLM_PPA SP_AA   3       1.63    3       1,3,5

This file is readily readable with `Pandas <https://pandas.pydata.org/>`_:

.. code:: python

    import pandas as pd
    data = pd.read_csv(filepath, sep=r"\s+")

Alternatively, one can use a helper method from ``connectome_tools`` package itself:

.. code:: python

    from connectome_tools.dataset import read_nsyn
    data = read_nsyn(filepath, mtypes=<list of mtypes to consider>)
