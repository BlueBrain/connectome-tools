Changelog
=========

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
