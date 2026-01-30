gen_gnsin
=========

Usage
-----

.. parsed-literal::

    cg_spica gen_gnsin -pdb <:strong:`pdbfile`> [-o <:strong:`output`>] [-pspica] [--toppar_dir <:strong:`dir`>]

Description
-----------

``gen_gnsin`` generates GENESIS control (input) files for SPICA or pSPICA CG-MD simulations.
This program reads box size information from a PDB file and creates an NPT ensemble control file
optimized for SPICA/pSPICA force fields. The program requires
``pdbfile`` for CG configuration file in PDB format with CRYST1 line containing box dimensions.
ENM files in ``toppar_dir`` directory are automatically detected and included in the parameter file list. In this case, No manual specification needed.
The generated control file contains settings specifically optimized for SPICA/pSPICA force fields,
including appropriate cutoff distances, PME parameters, and possible domain decomposition suggestions.


Example
-------

**Generate SPICA NPT input file:**

.. code-block:: bash

    cg_spica gen_gnsin -pdb dopc.cg.pdb

:download:`dopc.cg.pdb <data/dopc.cg.pdb>` 


**Generate pSPICA input file:**

.. code-block:: bash

    cg_spica gen_gnsin -pdb p_dopc.cg.pdb  -pspica

This sets ``pme_max_spacing = 2.0`` and ``fast_water = YES`` for polarizable water models.

:download:`p_dopc.cg.pdb <data/p_dopc.cg.pdb>`  


**Specify custom output filename:**

.. code-block:: bash

    cg_spica gen_gnsin -pdb dopc.cg.pdb -o production.inp

Positional args
---------------

``-pdb`` <.pdb>
    Input PDB file with box information (CRYST1 line required)

Optional args
-------------

``-o`` <output>
    Output control file name (default: npt.inp)

``-pspica``
    Use pSPICA-specific parameters:
    
    * pme_max_spacing = 2.0 (instead of 5.0 for SPICA)
    * fast_water = YES (instead of NO for SPICA)

``--toppar_dir`` <dir>
    Directory containing topology/parameter files (default: toppar)

Output File
-----------

The generated control file includes:

**[INPUT] section:**
    Topology, parameter, PSF, and PDB files. ENM files (``enm_bond_index.ndx``, 
    ``enm_bond_parm.prm``, ``enm_angle_index.ndx``, ``enm_angle_parm.prm``) are 
    automatically included if present in toppar directory.

**[ENERGY] section:**
    SPICA force field settings with PME electrostatics, cutoff=15Å, switch=12Å, 
    pairlist=18Å. Includes contact_check and nonb_limiter for ENM systems.

**[DYNAMICS] section:**
    VVER integrator, timestep=10fs, default 10000 steps (100ps test run)

**[ENSEMBLE] section:**
    NPT ensemble, BUSSI thermostat/barostat, T=310K, P=1.0atm

**[BOUNDARY] section:**
    PBC. Domain decomposition numbers with suggested values in comments.



Important Notes
---------------


**CRYST1 Line Required**
    PDB file must contain a CRYST1 line with box information:

    .. code-block:: none

        CRYST1  400.000  500.000  600.000  90.00  90.00  90.00 P 1           1

**Box Size Expansion**
    If the initial minimization fails, and there are no bonds at the PBC boundary, slightly expanding the box size as follows may resolve the issue. Box dimensions might be expanded by 1.02× to provide buffer space.
    E.g. Original: 400×500×600 Å → Simulation: 408×510×612 Å

**Domain Decomposition**
    The program calculates reasonable domain decomposition numbers based on:

* Minimum domain size: 100 Å per domain
* Valid numbers: Multiples of 2 or 3 (e.g., 2, 3, 4, 6, 8, 9, 10, 12, ...)
* Minimum count: 2 domains per dimension

For example, with box size 408 Å:

.. code-block:: none

    Maximum domains: floor(408 / 100) = 4
    Valid candidates: 2, 3, 4
    Output: domain_x = 2    # 2, 3, 4 is reasonable

Users can manually adjust domain_x/y/z values based on available MPI processes.
Total MPI processes must equal domain_x × domain_y × domain_z.

**MPI Requirements**
    GENESIS SPDYN requires at least 2 domains per dimension. Serial execution 
    is not supported. Minimum configuration: 2×2×2 = 8 MPI processes.
		This predicted value is based on empirical rules, and the actual maximum depends on the actual system size, pressure, and other factors. Therefore, please first confirm that the calculation runs without problems using 2x2x2, and then gradually increase the number of MPI processes.

See Also
--------

* :doc:`setup_gns` - Generate GENESIS topology and parameter files


