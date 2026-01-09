#!/usr/bin/env python3
"""
gen_gns_input: Generate GENESIS input file for SPICA/pSPICA simulations

This module reads box size from a PDB file and generates a GENESIS control file
for NPT ensemble MD simulations.
"""

import argparse
import sys
import os


def read_pdb_box(pdb_file):
    """
    Read box size information from CRYST1 line in PDB file.
    
    Parameters
    ----------
    pdb_file : str
        Path to PDB file
        
    Returns
    -------
    tuple
        (box_x, box_y, box_z) in Angstroms, or (None, None, None) if not found
    """
    box_x = box_y = box_z = None
    
    try:
        with open(pdb_file, 'r') as f:
            for line in f:
                if line.startswith('CRYST1'):
                    items = line.split()
                    if len(items) >= 4:
                        box_x = float(items[1])
                        box_y = float(items[2])
                        box_z = float(items[3])
                        break
    except FileNotFoundError:
        print(f"ERROR: PDB file not found: {pdb_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read PDB file: {e}", file=sys.stderr)
        sys.exit(1)
    
    return box_x, box_y, box_z


def check_enm_files(toppar_dir='toppar'):
    """
    Check which ENM files exist in the toppar directory.
    
    Parameters
    ----------
    toppar_dir : str
        Directory containing topology and parameter files
        
    Returns
    -------
    list
        List of existing ENM file paths
    """
    enm_files = [
        'enm_bond_index.ndx',
        'enm_bond_parm.prm',
        'enm_angle_index.ndx',
        'enm_angle_parm.prm'
    ]
    
    existing_files = []
    for fname in enm_files:
        fpath = os.path.join(toppar_dir, fname)
        if os.path.exists(fpath):
            existing_files.append(os.path.join(toppar_dir, fname))
    
    return existing_files


def calculate_domain_candidates(box_size, min_cell_size=100.0):
    """
    Calculate reasonable domain decomposition numbers.
    
    Domain number must be:
    - At least 2
    - Multiples of 2 or 3 (divisible by 2 or 3)
    - box_size / domain >= min_cell_size
    
    Parameters
    ----------
    box_size : float
        Box size in one dimension (Angstroms)
    min_cell_size : float
        Minimum cell size (default: 100.0 Angstroms)
        
    Returns
    -------
    list
        List of reasonable domain numbers
    """
    max_domain = int(box_size / min_cell_size)
    
    if max_domain < 2:
        return [2]
    
    candidates = []
    
    # Include all numbers from 2 to max_domain that are divisible by 2 or 3
    for n in range(2, max_domain + 1):
        if n % 2 == 0 or n % 3 == 0:
            candidates.append(n)
    
    return candidates if candidates else [2]


def generate_genesis_input(pdb_file, output_file='npt.inp', pspica=False, toppar_dir='toppar'):
    """
    Generate GENESIS control file for NPT MD simulation.
    
    Parameters
    ----------
    pdb_file : str
        Input PDB file containing coordinates and box information
    output_file : str
        Output control file name (default: npt.inp)
    pspica : bool
        Use pSPICA parameters (default: False)
    toppar_dir : str
        Directory containing topology and parameter files (default: toppar)
    """
    # Read box dimensions from PDB
    box_x0, box_y0, box_z0 = read_pdb_box(pdb_file)
    
    if box_x0 is None or box_y0 is None or box_z0 is None:
        print("ERROR: Box size information not found in PDB file.", file=sys.stderr)
        print("       CRYST1 line is required.", file=sys.stderr)
        sys.exit(1)
    
    # Calculate expanded box sizes (1.02x)
    box_x = box_x0 * 1.02
    box_y = box_y0 * 1.02
    box_z = box_z0 * 1.02
    
    print(f"Original box size: {box_x0:.2f} x {box_y0:.2f} x {box_z0:.2f} Ang")
    print(f"Expanded box size: {box_x:.2f} x {box_y:.2f} x {box_z:.2f} Ang")
    
    # Calculate domain decomposition candidates
    domain_x_candidates = calculate_domain_candidates(box_x)
    domain_y_candidates = calculate_domain_candidates(box_y)
    domain_z_candidates = calculate_domain_candidates(box_z)
    
    # Default to minimum (2)
    domain_x = 2
    domain_y = 2
    domain_z = 2
    
    print(f"\nRecommended domain decomposition:")
    print(f"  domain_x: {domain_x_candidates}")
    print(f"  domain_y: {domain_y_candidates}")
    print(f"  domain_z: {domain_z_candidates}")
    
    # Check for ENM files
    enm_files = check_enm_files(toppar_dir)
    
    # Build parfile line
    parfile_list = [f'{toppar_dir}/par_spica_charmm.prm']
    parfile_list.extend(enm_files)
    parfile_line = ', '.join(parfile_list)
    
    if enm_files:
        print(f"\nFound ENM files: {len(enm_files)}")
        for f in enm_files:
            print(f"  - {f}")
    
    # Set pSPICA-specific parameters
    if pspica:
        pme_max_spacing = 2.0
        fast_water = 'YES'
        print("\npSPICA mode: pme_max_spacing=2.0, fast_water=YES")
    else:
        pme_max_spacing = 5.0
        fast_water = 'NO'
        print("\nSPICA mode: pme_max_spacing=5.0, fast_water=NO")
    
    # Format domain candidate strings
    domain_x_str = ', '.join(map(str, domain_x_candidates))
    domain_y_str = ', '.join(map(str, domain_y_candidates))
    domain_z_str = ', '.join(map(str, domain_z_candidates))
    
    # Generate control file content
    content = f"""[INPUT]
topfile = {toppar_dir}/top_spica_charmm.rtf
parfile = {parfile_line}
psffile = gns_spica.psf
pdbfile = gns_spica.pdb
reffile = gns_spica.pdb
# rstfile = equilibrated.rst
 
[OUTPUT]
rstfile = mdout.rst
dcdfile = mdout.dcd

[ENERGY]
forcefield      = SPICA        # [CHARMM]
electrostatic   = PME           # [CUTOFF,PME]
switchdist      = 12.0          # switch distance
cutoffdist      = 15.0          # cutoff distance
pairlistdist    = 18.0          # pair-list distance
pme_nspline     = 4
water_model     = NONE
vdw_force_switch = NO
pme_max_spacing = {pme_max_spacing}

contact_check   = YES          # avoid atomic crash
nonb_limiter    = YES # for large ENM system, you need to use this even for NPT
minimum_contact = 0.5
force_max_assign = YES
force_max       = 100.0

[DYNAMICS]
integrator      = VVER          # [LEAP,VVER]
timestep        = 0.01        # timestep (ps)
nsteps          = 10000        # short test
crdout_period   = 10000
eneout_period   = 1000          # energy output period
rstout_period   = 10000      
nbupdate_period = 10 
# MTS の場合は次
# elec_long_period = 5
# thermostat_period = 10
# barostat_period = 10
 
[CONSTRAINTS]
rigid_bond      = NO           # constraints all bonds involving hydrogen
fast_water      = {fast_water}
shake_tolerance = 1.0D-10

[ENSEMBLE]
ensemble        = NPT           # [NVE,NVT,NPT]
tpcontrol       = BUSSI      # thermostat and barostat
temperature     = 310
pressure        = 1.0           # atm
isotropy        = ISO

[BOUNDARY]
type            = PBC           # [PBC]
box_size_x      = {box_x:.3f}
box_size_y      = {box_y:.3f}
box_size_z      = {box_z:.3f}
domain_x = {domain_x}    # {domain_x_str} is reasonable
domain_y = {domain_y}    # {domain_y_str} is reasonable
domain_z = {domain_z}    # {domain_z_str} is reasonable
"""
    
    # Write to file
    try:
        with open(output_file, 'w') as f:
            f.write(content)
        print(f"\nGENESIS control file generated: {output_file}")
    except Exception as e:
        print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)


def get_option_script(args):
    """Parse command-line arguments for cg_spica integration"""
    parser = argparse.ArgumentParser(
        description='Generate GENESIS input file for SPICA/pSPICA CG simulations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-pdb', '--pdb', required=True,
                        help='Input PDB file with box information (CRYST1 line)')
    parser.add_argument('-o', '--output', default='npt.inp',
                        help='Output control file name (default: npt.inp)')
    parser.add_argument('-pspica', '--pspica', action='store_true',
                        help='Use pSPICA parameters (pme_max_spacing=2, fast_water=YES)')
    parser.add_argument('--toppar_dir', default='toppar',
                        help='Directory containing topology/parameter files (default: toppar)')
    
    return parser.parse_args(args)


def run(args):
    """Main execution function for cg_spica integration"""
    if not os.path.exists(args.pdb):
        print(f"ERROR: PDB file not found: {args.pdb}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(args.toppar_dir):
        print(f"WARNING: toppar directory not found: {args.toppar_dir}", file=sys.stderr)
        print(f"         Please make sure topology files exist before running GENESIS.", file=sys.stderr)
    
    generate_genesis_input(args.pdb, args.output, args.pspica, args.toppar_dir)
    
    print("\nDone. Please check the generated input file before running simulation.")
    print("Remember to prepare topology files using setup_gns first if not done.")
    print("\nTo run the simulation:")
    print("  export OMP_NUM_THREADS=4")
    print("  mpirun -n 8 spdyn npt.inp > npt.log")


if __name__ == '__main__':
    args = get_option_script(sys.argv[1:])
    run(args)
