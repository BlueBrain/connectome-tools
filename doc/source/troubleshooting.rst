Troubleshooting
===============


Running in a sbatch script
--------------------------

The tools ``s2f-recipe-merge``, ``s2f-recipe`` and ``connectome-stats`` should not be executed using ``srun``,
because ``srun`` could launch multiple instances of them.

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


Stopping s2f-recipe-merge
-------------------------

If for any reason ``s2f-recipe-merge`` is stopped before the completion, it's possible that some slurm jobs
will continue to run in the background.

Any related job should be stopped before running again the script with the same configuration, or
it's possible that multiple jobs will try to generate the same recipe file.

To verify the list of slurm jobs, it's possible to execute:

.. code-block:: bash

    squeue -u $USER -n "<job-name>"

All the related pending jobs can be cancelled at once by specifying the job ID of the job array
without the array ID suffix:

.. code-block:: bash

    scancel "<job-id-without-array-id>"
