Tools
=====

connectome-stats
----------------

Sample connectome statistics from the circuit, dump as a *dataset* specified above.

Usage:

.. code-block:: console

    $ module load unstable connectome-tools
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

would produce a `bouton-density <#ref-dataset-bouton-density>`_ dataset for a given circuit.

Options:

    -n, --sample-size INTEGER   Sample size  [default: ``100``]
    -t, --sample-target TEXT    Sample target [default: ``None``]
    --mask TEXT                 Region of interest [default: ``None``]
    --assume-syns-bouton FLOAT  Synapse count per bouton  [default: ``1.0``]
    --short                     Omit sampled values from the output [default: ``False``]

Optional ``--mask`` parameter references atlas dataset with volumetric mask defining axon region of interest.
If provided, only axonal segments within this region would be considered for each sampled cell (otherwise whole axon is considered, without any filtering). Please note that this parameter does *not* affect cell sampling (i.e., the choice of cell somata is affected only by ``--sample-target``).

Circuit model source atlas defined in CircuitConfig is used for filtering segments. If VoxelBrain URL is provided there, please set ``BLUEPY_ATLAS_CACHE_DIR`` environment variable to define the folder for storing data fetched from VoxelBrain.

Please note also that using region filtering might affect the performance.

It is generally recommended to limit sample target and / or region mask to circuit "center" to minimize border effects (for instance, using central hypercolumn in O1 mosaic circuit, as in the example above).

If there are only ``K`` < ``SAMPLE_SIZE`` samples available, ``K`` samples will be used.

connectome-stats nsyn-per-connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    $ connectome-stats --seed 0 nsyn-per-connection -n 5 <CircuitConfig>

would produce a `nsyn-per-connection <#ref-dataset-nsyn-per-connection>`_ dataset for a given circuit.

Options:

  -n, --sample-size INTEGER  Sample size  [default: ``100``]
  --pre TEXT                 Presynaptic target [default: ``None``]
  --post TEXT                Postsynaptic target [default: ``None``]
  --short                    Omit sampled values  [default: ``False``]

If there are only ``K`` < ``SAMPLE_SIZE`` samples available, ``K`` samples will be used.

If no sample is available (i.e. two mtypes are not connected), the result row will get ``N/A`` values.


s2f-recipe
----------

Generate XML recipe to be used by `Functionalizer <https://bbpteam.epfl.ch/documentation/projects/functionalizer/latest/>`_  or `Spykfunc <https://bbpteam.epfl.ch/documentation/projects/spykfunc/latest/index.html>`_ for synapse pruning according to the algorithm described `here <https://www.frontiersin.org/articles/10.3389/fncom.2015.00120/full>`_.

Usage:

.. code:: console

    s2f-recipe -s STRATEGIES -o OUTPUT [--seed SEED] [-v] <CircuitConfig>

Options:
    -s, --strategies TEXT  Path to strategies config (YAML)  [required]
    -o, --output TEXT      Path to output file (XML)  [required]
    -v, --verbose          -v for INFO, -vv for DEBUG
    --seed INTEGER         Pseudo-random generator seed  [default: 0]
    -j, --jobs INTEGER     Maximum number of concurrently running jobs (if -1
                           all CPUs are used)  [default: -1]

For better performance, it's recommended to run the script specifying multiple concurrent jobs.

Since version 0.6.0 the output is an XML file of form:

::

    <ConnectionRules>
        <rule fromMType="from_1" toMType="to_1" cv_syns_connection="0.348" bouton_reduction_factor="0.459" mean_syns_connection="4.341" />
        <rule fromMType="from_2" toMType="to_2" cv_syns_connection="0.348" bouton_reduction_factor="0.184" mean_syns_connection="3.470" />
        <rule fromMType="from_3" toMType="to_3" bouton_reduction_factor="1.000" p_A="1.000" pMu_A="0.000"/>
        ...
    </ConnectionRules>

For each ``(from_K, to_K)`` pathway, `strategies` define the values of one of the two
possible sets of resulting parameters:

    - ``bouton_reduction_factor``, ``cv_syns_connection``, ``mean_syns_connection``
    - ``bouton_reduction_factor``, ``p_A``, ``pMu_A``

Available strategies:

    - ``estimate_bouton_reduction``
    - ``estimate_individual_bouton_reduction``
    - ``estimate_syns_con``
    - ``existing_recipe``
    - ``experimental_syns_con``
    - ``generalized_cv``
    - ``override_mtype``
    - ``add_constraints``

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
    - add_constraints:
        fromRegion: mc2_Column

Each strategy deduces one or several ``<rule>`` parameters for a subset of pathways.

Values defined by latter strategies take precedence over the earlier ones.

We'll go through each of the available strategies one by one.

estimate_bouton_reduction
~~~~~~~~~~~~~~~~~~~~~~~~~

Estimate an overall reduction factor based on an estimated mean bouton density over all mtypes.

Outputs the `bouton_reduction_factor`_ constraint

Parameters:

**bio_data**
    Path to `bouton-density <#ref-dataset-bouton-density>`_ dataset representing reference biological data (OR single float value)

**sample**
    Parameters for sampling bouton density OR path to `bouton-density <#ref-dataset-bouton-density>`_ dataset already sampled from the circuit


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

Outputs the `bouton_reduction_factor`_ constraint

Parameters are analogous to those of `estimate_bouton_reduction` strategy.


estimate_syns_con
~~~~~~~~~~~~~~~~~

Estimate the functional mean number of synapses per connection from the structural number of appositions per connection. For the prediction, an algebraic expression using 'n' (mean number of appositions) should be specified.

Outputs the `mean_syns_connection`_ constraint

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
    Parameters for sampling nsyn per connection OR path to `nsyn-per-connection <#ref-dataset-nsyn-per-connection>`_ dataset already sampled from the circuit

If **sample** is a set of parameters for sampling, it can include any of the following keys:

**pre**
    Presynaptic target [default: ``None``]

**post**
    Postsynaptic target [default: ``None``]

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

Outputs the `mean_syns_connection`_ constraint

Parameters:

**bio_data**
    Path to `nsyn-per-connection <#ref-dataset-nsyn-per-connection>`_ dataset representing reference biological data

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
    ``bouton_reduction_factor`` value to use.

**mean_syns_connection**
    ``mean_syns_connection`` value to use.

**cv_syns_connection**
    ``cv_syns_connection`` value to use.

**p_A**
    ``p_A`` value to use as reduction factor. It can be specified together with ``pMu_A``
    as an alternative to ``mean_syns_connection`` and ``cv_syns_connection``.

**pMu_A**
    ``pMu_A`` value to use as input to the survival rate. It can be specified together with ``p_A``
    as an alternative to ``mean_syns_connection`` and ``cv_syns_connection``.

Example 1:

::

    - override_mtype:
        mtype_pattern: CHC
        bouton_reduction_factor: 1.0
        mean_syns_connection: 1.0
        cv_syns_connection: 1.0

Example 2:

::

    - override_mtype:
        mtype_pattern: CHC
        bouton_reduction_factor: 1.0
        p_A: 1.0
        pMu_A: 0.0


add_constraints
~~~~~~~~~~~~~~~

Set generic constraints that will be added to the generated rules for all the pathways.
It can be used to specify one or more selection attributes such as ``fromRegion`` and ``toRegion``.
Note that no checks are made, and that the constraints must be added accordingly
with the rest of the strategies.

Example:

::

    - add_constraints:
        fromRegion: mc2_Column


Troubleshooting
===============

The tools ``s2f-recipe`` and ``connectome-stats`` should not be executed using ``srun``, because ``srun`` could launch multiple instances of them.

Starting from version `0.3.4`, the script will terminate if it detects that another instance is running.

If you are running the command using a sbatch script, verify that ``srun`` is not used.

This is an example of a minimal script for ``s2f-recipe``, running one instance of the program on a
single exclusive node, without using ``srun``:

.. code-block:: bash

    #!/bin/bash
    #SBATCH --job-name="<job-name>"
    #SBATCH --qos="<qos>"
    #SBATCH --time="<time>"
    #SBATCH --nodes=1
    #SBATCH --mem=0
    #SBATCH --exclusive
    #SBATCH --constraint=cpu
    #SBATCH --partition="<partition>"
    #SBATCH --account="<projXX>"
    set -eu

    module load "archive/<YYYY-MM>"
    module load connectome-tools

    s2f-recipe <OPTIONS AND ARGUMENTS>


.. _bouton_reduction_factor: https://bbpteam.epfl.ch/documentation/projects/Circuit%20Documentation/latest/recipe.html#bouton-reduction-factor
.. _mean_syns_connection: https://bbpteam.epfl.ch/documentation/projects/Circuit%20Documentation/latest/recipe.html#mean-syns-connection

