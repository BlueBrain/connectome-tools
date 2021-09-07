Changelog
=========

Version 0.6.1
-------------

New Features
~~~~~~~~~~~~
- Allow to specify the parameter ``slurm_srun_args`` to be able to execute ``srun --mpi=none``
  and avoid the MPI error ``MPT ERROR: PMI2_Init`` when using spack modules.
- Define a default value for the executor parameters.
- Update the documentation.


Version 0.6.0
-------------

New Features
~~~~~~~~~~~~
- Update the names used in the recipe to use the new format. [NSETM-1451]
- Allow to specify the selection attributes in the new strategy ``add_constraints``. [NSETM-1450]
- Add ``s2f-recipe-merge`` to run multiple ``s2f-recipe`` commands split by region
  and merge the results. [NSETM-1450]
- Drop support for python 3.6 and 3.7.
- Update the documentation.


Version 0.5.1
-------------

Improvements
~~~~~~~~~~~~

- Check for duplicate rows in .tsv files (bouton density data and nsyn). [NSETM-1512]

Bug Fixes
~~~~~~~~~
- Fix section ID numbering in the function that calculates the bouton density,
  needed for compatibility with BluePy 2.3.0. [NSETM-1477]
- Sum the length of all the axons to calculate the bouton density, in the unlikely case
  of neurons with multiple axons.


Version 0.5.0
-------------

New Features
~~~~~~~~~~~~
- Add parameter ``n_jobs`` in ``stats.sample_bouton_density`` for parallel execution.

Improvements
~~~~~~~~~~~~
- Parallelize strategy ``estimate_bouton_reduction`` in ``s2f-recipe``. [NSETM-1435]
- Change the parallelization of the strategy ``estimate_individual_bouton_reduction``
  in ``s2f-recipe``. [NSETM-1435]

  Now the values for each pathway are computed sequentially,
  but the computation of the value for a single pathway is parallelized.

  The gids are split in chunks to reduce the number of tasks submitted to the subprocesses,
  and it's possible to specify the minimum number of gids to be processed in a single job
  setting the env variable ``MIN_GIDS_PER_JOB`` (default 1).

Version 0.4.1
-------------

New Features
~~~~~~~~~~~~
- Add support for analysis of bouton density and synapse counts in projections.


Bug Fixes
~~~~~~~~~~~~
- Change the old hidden variable from bluepy _PRE_SEGMENT_ID to the new one Synapse.PRE_SEGMENT_ID


Version 0.4.0
-------------

Improvements
~~~~~~~~~~~~
- Support and require Bluepy >= 2.0.


Version 0.3.4
-------------

Improvements
~~~~~~~~~~~~
- Ensure that only one instance of s2-recipe or connectome-stats is running. [NSETM-1322]


Version 0.3.3
-------------

New Features
~~~~~~~~~~~~
- Add support for `p_A` and `pMu_A` parameters. [NSETM-1096]


Bug Fixes
~~~~~~~~~~~~
- If formula result for `estimate_syns_con` is NaN, it's now considered as 1.0. [NSETM-1137]


Removed Features
~~~~~~~~~~~~~~~~
- Drop support for Python 2.7.


Improvements
~~~~~~~~~~~~
- Add ``--jobs`` option to parallelize tasks. [NSETM-1102]
