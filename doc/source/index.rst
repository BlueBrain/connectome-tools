Introduction
============

``connectome-tools`` package is a collection of tools for specifying and analysing circuit connectivity.

It relies on `BluePy <https://bbpcode.epfl.ch/documentation/bluepy-0.11.14/>`_ for accessing circuit data.

At the moment two tools are provided:

**connectome-stats**
    Sampling some connectome statistics from the circuit.

**s2f-recipe**
    Writing synapse pruning recipe used by `Functionalizer <https://bbpteam.epfl.ch/documentation/functionalizer-3.11.0/index.html>`_.


.. contents::
   :depth: 2


Installation
============

module load
-----------

The easiest way to get ``connectome-tools`` package might be with a *module*:

.. code-block:: console

    $ module load nix/nse/connectome-tools


To ensure the result obtained with the tools is reproducible, please consider using a specific `BBP archive S/W module <https://bbpteam.epfl.ch/project/spaces/display/BBPHPC/BBP+ARCHIVE+SOFTWARE+MODULES>`_.

pip install
-----------

Alternatively, ``connectome-tools`` is also distributed as a Python package available at BBP devpi server:

.. code-block:: console

    $ pip install -i https://bbpteam.epfl.ch/repository/devpi/simple/ connectome-tools

Only Python 2.7 / Python 3.5+ is supported at the moment.

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


Tools
=====

connectome-stats
----------------

Sample connectome statistics from the circuit, dump as a *dataset* specified above.

Usage:

.. code-block:: console

    $ module load nix/nse/connectome-tools
    $ connectome-stats [OPTIONS] COMMAND [ARGS] <CircuitConfig>

Options:

  --seed INTEGER  Random generator seed

Commands:

    - ``bouton-density``
    - ``nsyn-per-connection``


connectome-stats bouton-density
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    $ connectome-stats --seed 0 bouton-density -t mc2_Column -n 5 --assume-syns-bouton 1.15 <CircuitConfig>

would produce a :ref:`ref-dataset-bouton-density` dataset for a given circuit.

Options:

    -n, --sample-size INTEGER   Sample size  [default: ``100``]
    -t, --sample-target TEXT    Sample target [default: ``None``]
    --mask TEXT                 Region of interest [default: ``None``]
    --assume-syns-bouton FLOAT  Synapse count per bouton  [default: ``1.0``]
    --short                     Omit sampled values from the output [default: ``False``]

Optional ``--mask`` parameter references atlas dataset with volumetric mask defining region of interest.
If provided, only axonal segments within this region would be considered for each sampled cell (otherwise whole axon is considered, without any filtering).
Circuit model source atlas defined in CircuitConfig is used for filtering segments. If VoxelBrain URL is provided there, please set ``BLUEPY_ATLAS_CACHE_DIR`` environment variable to define the folder for storing data fetched from VoxelBrain.
Please note also that using region filtering might affect the performance.

It is generally recommended to limit sample target and / or region to circuit "center" to minimize border effects (for instance, using central hypercolumn in O1 mosaic circuit, as in the example above).

If there are only ``K`` < ``SAMPLE_SIZE`` samples available, ``K`` samples will be used.

connectome-stats nsyn-per-connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    $ connectome-stats --seed 0 nsyn-per-connection -n 5 <CircuitConfig>

would produce a :ref:`ref-dataset-nsyn-per-connection` dataset for a given circuit.

Options:

  -n, --sample-size INTEGER  Sample size  [default: ``100``]
  --short                    Omit sampled values  [default: ``False``]

If there are only ``K`` < ``SAMPLE_SIZE`` samples available, ``K`` samples will be used.

If no sample is available (i.e. two mtypes are not connected), the result row will get ``N/A`` values.


s2f-recipe
----------

Generate XML recipe to be used by `Functionalizer <https://bbpteam.epfl.ch/documentation/functionalizer-3.11.0/index.html>`_ for synapse pruning according to the algorithm described `here <https://www.frontiersin.org/articles/10.3389/fncom.2015.00120/full>`_.

Usage:

.. code:: console

    s2f-recipe -s STRATEGIES -o OUTPUT [--seed SEED] [-v] <CircuitConfig>

Options:
    -s, --strategies TEXT   Path to strategies config (YAML)
    -o, --output OUTPUT     Path to output file (XML)
    -v, --verbose           Log verbosity level
    --seed SEED             Random generator seed

The output is an XML file of form:

::

    <ConnectionRules>
        <mTypeRule from="from_1" to="to_1" cv_syns_connection="0.348" bouton_reduction_factor="0.459" mean_syns_connection="4.341" />
        <mTypeRule from="from_2" to="to_2" cv_syns_connection="0.348" bouton_reduction_factor="0.184" mean_syns_connection="3.470" />
        ...
    </ConnectionRules>

`strategies` define how ``cv_syns_connection``, ``bouton_reduction_factor``, ``mean_syns_connection`` values are defined for each ``(from_K, to_K)`` pathway.

Available strategies:

    - ``estimate_bouton_reduction``
    - ``estimate_individual_bouton_reduction``
    - ``estimate_syns_con``
    - ``existing_recipe``
    - ``experimental_syns_con``
    - ``generalized_cv``
    - ``override_mtype``

The sequence of strategies applied along with their arguments is defined by YAML file, for example:

::

    - estimate_syns_con:
        formula: 6 * ((n - 1) ** 0.5) - 1
        formula_ee: 1.5 * n
        max_value: 25.0
        sample:
            size: 1000
    - experimental_syns_con:
        bio_data: /gpfs/bbp.cscs.ch/project/proj64/entities/dev/datasets/nsyn_per_connection_20160509_full.tsv
    - estimate_bouton_reduction:
        bio_data: /gpfs/bbp.cscs.ch/project/proj64/entities/dev/datasets/bouton_density_20161102.tsv
        sample:
            size: 100
            target: mc2_Column
            mask: mc2_Column
            assume_syns_bouton: 1.2
    - estimate_individual_bouton_reduction:
        bio_data: /gpfs/bbp.cscs.ch/project/proj64/entities/dev/datasets/bouton_density_20161102.tsv
        sample:
            size: 100
            target: mc2_Column
            mask: mc2_Column
            assume_syns_bouton: 1.2
    - generalized_cv:
        cv: 0.32
    - override_mtype:
        mtype_pattern: CHC
        bouton_reduction_factor: 1.0
        mean_syns_connection: 1.0
        cv_syns_connection: 1.0

Each strategy deduces one or several ``<mTypeRule>`` parameters for a subset of pathways.

Values defined by latter strategies take precedence over the earlier ones.

We'll go through each of the available strategies one by one.

estimate_bouton_reduction
~~~~~~~~~~~~~~~~~~~~~~~~~

Estimate an overall reduction factor based on an estimated mean bouton density over all mtypes.

Parameters:

**bio_data**
    Path to :ref:`ref-dataset-bouton-density` dataset representing reference biological data (OR single float value)

**sample**
    Parameters for sampling bouton density OR path to :ref:`ref-dataset-bouton-density` dataset already sampled from the circuit


If **sample** is a set of parameters for sampling, it can include any of the following keys:

**size**
    Sample size [default: ``100``]

**target**
    Sample target [default: ``None``]

**mask**
    | Region of interest [default: ``None``].
    | If provided, only axonal segments within this region would be considered.

**assume_syns_bouton**
    Assumed synapse count per bouton [default: ``1.0``]

Bouton density datasets used should include '*' entry, which stands for sample over all mtypes.

Example 1:

::

    - estimate_bouton_reduction:
        bio_data: 0.432
        sample:
            size: 100
            target: 'mc2_Column'
            mask: 'center'
            assume_syns_bouton: 1.2

Example 2:

::

    - estimate_bouton_reduction:
        bio_data: /gpfs/bbp.cscs.ch/project/proj64/entities/dev/datasets/bouton_density_20161102.tsv
        sample: /gpfs/bbp.cscs.ch/project/proj64/circuits/O1.v6a/20171113/ncsStructural/bouton_density_mc2_Column_1.2_1000.tsv


estimate_individual_bouton_reduction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Estimate a reduction factor for each individual mtype, where experimental data is available.

Parameters are analogous to those of `estimate_bouton_reduction` strategy.

estimate_syns_con
~~~~~~~~~~~~~~~~~

Estimate the functional mean number of synapses per connection from the structural number of appositions per connection. For the prediction, an algebraic expression using 'n' (mean number of appositions) should be specified.

Parameters:

**formula**
    Synapse number prediction formula [required].

**formula_ee**
    Synapse number prediction formula for EXC->EXC pathways.
    Optional, if omitted, general `formula` would be used

**formula_ei**
    Synapse number prediction formula for EXC->INH pathways.
    Optional, if omitted, general `formula` would be used

**formula_ie**
    Synapse number prediction formula for INH->EXC pathways.
    Optional, if omitted, general `formula` would be used

**formula_ii**
    Synapse number prediction formula for INH->INH pathways.
    Optional, if omitted, general `formula` would be used

**max_value**
    Max value for predicted synapse number.
    Optional, if omitted, the predicted synapse number is not clipped above
    NB: predicted synapse value would be always min-clipped to 1.0 to avoid invalid synapse count values.

**sample**
    Parameters for sampling nsyn per connection OR path to :ref:`ref-dataset-nsyn-per-connection` dataset already sampled from the circuit

If **sample** is a set of parameters for sampling, it can include any of the following keys:

**size**
    Sample size [default: ``100``]

Example 1:

::

    - estimate_syns_con:
        formula: 6 * ((n - 1) ** 0.5) - 1
        formula_ee: 1.5 * n
        max_value: 25.0
        sample:
            size: 1000

Example 2:

::

    - estimate_syns_con:
        formula: 1.0 * n
        sample: /gpfs/bbp.cscs.ch/project/proj64/circuits/O1.v6a/20171113/ncsStructural/nsyn_per_connection_1000.tsv


existing_recipe
~~~~~~~~~~~~~~~

Take parameters from already existing S2F recipe (XML).

Parameters:

**recipe_path**
    Path to existing S2F recipe

experimental_syns_con
~~~~~~~~~~~~~~~~~~~~~

Use the biological mean number of synapses per connection for a number of pathways where experimental data is available.

Parameters:

**bio_data**
    Path to :ref:`ref-dataset-nsyn-per-connection` dataset representing reference biological data

generalized_cv
~~~~~~~~~~~~~~

Set ``cv_syns_connection`` value for all pathways.

Parameters:

**cv**
    ``cv_syns_connection`` value to use


override_mtype
~~~~~~~~~~~~~~

Set parameters for a subset of *to* mtypes.

Parameters:

**mtype_pattern**
    Substring to look for in mtype.

**bouton_reduction_factor**
    ``bouton_reduction_factor`` value to use

**mean_syns_connection**
    ``mean_syns_connection`` value to use

**cv_syns_connection**
    ``cv_syns_connection`` value to use

Example:

::

    - override_mtype
        mtype_pattern: CHC
        bouton_reduction_factor: 1.0
        mean_syns_connection: 1.0
        cv_syns_connection: 1.0


Acknowledgments
===============

``connectome-tools`` is a refactored subset of ``bluerecipe`` toolset originally developed by `Michael Reimann <mailto:michael.reimann@epfl.ch>`_.


Reporting issues
================

``connectome-tools`` is maintained by BlueBrain NSE team at the moment.

Should you face any issue with using it, please submit a ticket to our `issue tracker <https://bbpteam.epfl.ch/project/issues/browse/NSETM>`_; or drop us an `email <mailto: bbp-ou-nse@groupes.epfl.ch>`_.