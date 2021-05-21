Changelog
=========

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
