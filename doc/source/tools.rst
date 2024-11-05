Tools
=====

connectome-stats
----------------

Sample connectome statistics from the circuit, dump as a *dataset* specified above.

Usage:

.. code-block:: console

    $ module load unstable connectome-tools
    $ connectome-stats [OPTIONS] COMMAND [ARGS] <circuit_config>

Options:

  --seed INTEGER  Random generator seed

Commands:

    - ``bouton-density``
    - ``nsyn-per-connection``


connectome-stats bouton-density
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    $ connectome-stats --seed 0 bouton-density -p <edge_population> -t mc2_Column -n 5 --assume-syns-bouton 1.15 <circuit_config>

would produce a `bouton-density <#ref-dataset-bouton-density>`_ dataset for a given circuit.

Options:

    -p, --edge-population TEXT  Edge population name  [required]
    -a, --atlas TEXT            Circuit atlas path [default: ``None``]
    -n, --sample-size INTEGER   Sample size  [default: ``100``]
    --neurite-type              Neurite type [default: ``axon``]
    -t, --node-set TEXT         Sample node set [default: ``None``]
    --mask TEXT                 Region of interest [default: ``None``]
    --assume-syns-bouton FLOAT  Synapse count per bouton  [default: ``1.0``]
    --short                     Omit sampled values from the output [default: ``False``]

Optional ``--mask`` parameter references atlas dataset with volumetric mask defining region of interest.
If provided, only segments within this region would be considered for each sampled cell (otherwise whole neurite is considered, without any filtering). Please note that this parameter does *not* affect cell sampling (i.e., the choice of cell somata is affected only by ``--node-set``).

Atlas provided as a commandline argument is used for filtering segments. If VoxelBrain URL is provided there, current working directory is used as atlas cache directory for storing data fetched from VoxelBrain.

Please note also that using region filtering might affect the performance.

It is generally recommended to limit sample node set and / or region mask to circuit "center" to minimize border effects (for instance, using central hypercolumn in O1 mosaic circuit, as in the example above).

If there are only ``K`` < ``SAMPLE_SIZE`` samples available, ``K`` samples will be used.

connectome-stats nsyn-per-connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: console

    $ connectome-stats --seed 0 nsyn-per-connection -p <edge_population> -n 5 <circuit_config>

would produce a `nsyn-per-connection <#ref-dataset-nsyn-per-connection>`_ dataset for a given circuit.

Options:
  -p, --edge-population TEXT Edge population name  [required]
  -n, --sample-size INTEGER  Sample size  [default: ``100``]
  --pre TEXT                 Presynaptic node set [default: ``None``]
  --post TEXT                Postsynaptic node set [default: ``None``]
  --short                    Omit sampled values  [default: ``False``]

If there are only ``K`` < ``SAMPLE_SIZE`` samples available, ``K`` samples will be used.

If no sample is available (i.e. two mtypes are not connected), the result row will get ``N/A`` values.


s2f-recipe
----------

Generate XML recipe to be used by `Functionalizer <https://bbpteam.epfl.ch/documentation/projects/functionalizer/latest/>`_  or `Spykfunc <https://bbpteam.epfl.ch/documentation/projects/spykfunc/latest/index.html>`_ for synapse pruning according to the algorithm described `here <https://www.frontiersin.org/articles/10.3389/fncom.2015.00120/full>`_.

Usage:

.. code:: console

    s2f-recipe -p <edge_population> -s STRATEGIES -o OUTPUT [--seed SEED] [-v] <circuit_config>

Options:
    -p, --edge-population TEXT  Edge population name  [required]
    -a, --atlas TEXT            Circuit atlas path [default: ``None``]
    -s, --strategies TEXT       Path to strategies config (YAML)  [required]
    -o, --output TEXT           Path to output file (XML)  [required]
    -v, --verbose               -v for INFO, -vv for DEBUG
    --seed INTEGER              Pseudo-random generator seed  [default: 0]
    -j, --jobs INTEGER          Maximum number of concurrently running jobs (if -1
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
            node_set: mc2_Column
            mask: mc2_Column
            assume_syns_bouton: 1.2
    - estimate_individual_bouton_reduction:
        bio_data: /gpfs/bbp.cscs.ch/project/proj64/entities/dev/datasets/bouton_density_20161102.tsv
        sample:
            size: 100
            node_set: mc2_Column
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

**node_set**
    Sample node set [default: ``None``]

**mask**
    | Region of interest [default: ``None``].
    | If provided, only segments within this region would be considered.

**assume_syns_bouton**
    Assumed synapse count per bouton [default: ``1.0``]

Bouton density datasets used should include '*' entry, which stands for sample over all mtypes.

Example 1:

::

    - estimate_bouton_reduction:
        bio_data: 0.432
        sample:
            size: 100
            node_set: 'mc2_Column'
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
    Presynaptic node set [default: ``None``]

**post**
    Postsynaptic node set [default: ``None``]

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

Overrides parameters for specific efferent mtypes.
This strategy is to be used last.

Parameters:

**mtype_pattern**
    Pattern, or list of patterns, used to match the mtype.

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

Set generic constraints that will be blindly added to the generated rules for all the pathways.
It can be used to specify one or more selection attributes such as ``fromRegion`` and ``toRegion``.

Note that no checks are made, and that the constraints must be added accordingly
with the rest of the strategies.

The allowed constraints are:

- fromRegion
- toRegion
- fromEType
- toEType
- fromSType
- toSType

Example:

::

    - add_constraints:
        fromRegion: mc2_Column


s2f-recipe-merge
----------------

Execute `s2f-recipe`_ for different regions, merging the results into a single recipe.
The partial recipes are concatenated in the same order as they are specified in the configuration file.


Usage:

.. code:: console

    $ s2f-recipe-merge [OPTIONS] COMMAND [ARGS]

Commands:

    - ``run``: S2F recipe generation with tasks split and merged by region.
    - ``clean``: Delete all the partial recipes and slurm logs.


s2f-recipe-merge run
~~~~~~~~~~~~~~~~~~~~

Use the given configuration files to run ``s2f-recipe`` and produce the recipe for the given circuit.

The partial recipes for each region and the log files are written into the working directory,
and they are reused if the script is stopped and restarted using the same configuration.

.. code:: console

    $ s2f-recipe-merge run -c MERGE_CONFIG -p EXECUTOR_CONFIG -o OUTPUT [--seed SEED] [-v] <circuit_config>

Options:

    -c, --config FILE           Path to the merge config file (YAML)  [required]
    -p, --edge-population TEXT  Edge population name  [required]
    -a, --atlas TEXT            Circuit atlas path [default: ``None``]
    -e, --executor-config FILE  Path to the executor config file (YAML) [required]
    -o, --output FILE           Path to the output file (XML)  [required]
    -w, --workdir PATH          Path to the working directory  [default: ``.s2f_recipe``]
    -v, --verbose               -v for INFO, -vv for DEBUG
    --seed INTEGER              Pseudo-random generator seed  [default: ``0``]
    -j, --jobs INTEGER          Maximum number of concurrently running jobs (if -1 all CPUs are used)  [default: ``-1``]


merge config
++++++++++++

The merge configuration file should contain the strategies for each region.

Each block of strategies must be compatible with the format used by ``s2f-recipe``,
and should contain the `add_constraints`_ strategy to specify the correct region,
that will be added blindly to all the rules of that region.

Example:

.. code-block:: yaml

    version: 1
    regions:
      - strategies:
        - ...
        - add_constraints:
            fromRegion: Mosaic
      - strategies:
        - ...
        - add_constraints:
            fromRegion: S1HL


executor config
+++++++++++++++

The executor configuration file should contain the slurm parameters used to run ``s2f-recipe``.

Each script is executed on a different node, and it's possible to define the maximum number of
nodes reserved at the same time.

Default configuration:

.. literalinclude:: ../../connectome_tools/data/default_config/executor_config.yaml
   :language: yaml

| The parameters marked with ``FIX`` should be overridden by the user configuration.
| A minimal user configuration could include just those keys like in the following example:

.. code-block:: yaml

    version: 1
    executor:
      slurm_array_parallelism: 20  # number of maximum concurrent nodes to be reserved (int)
      slurm_job_name: 's2f_recipe_merge'  # custom job name (str)
      slurm_time: 1440  # maximum allowed time per job, in minutes (int)
      slurm_additional_parameters:
        account: 'projXX'  # correct projXX (str)

Other slurm parameters can be added if needed.
For example, it's possible to specify a longjob qos with ``slurm_qos: 'longjob'``.


s2f-recipe-merge clean
~~~~~~~~~~~~~~~~~~~~~~

Delete all the partial recipes and slurm logs in the given working directory.

This can be useful to remove the temporary files when they are not needed anymore, for example after
the final recipe has been generated successfully, or to start again with a clean working directory.

.. code:: console

    $ s2f-recipe-merge clean [-w WORKDIR] [-v]

Options:
    -w, --workdir PATH  Path to the working directory to clean  [default: ``.s2f_recipe``]



.. _bouton_reduction_factor: https://bbpteam.epfl.ch/documentation/projects/Circuit%20Documentation/latest/recipe.html#bouton-reduction-factor
.. _mean_syns_connection: https://bbpteam.epfl.ch/documentation/projects/Circuit%20Documentation/latest/recipe.html#mean-syns-connection

