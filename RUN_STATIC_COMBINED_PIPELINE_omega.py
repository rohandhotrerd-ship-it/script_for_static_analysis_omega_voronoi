# -*- coding: mbcs -*-
"""
RUN_STATIC_COMBINED_PIPELINE_omega.py

Abaqus/CAE noGUI script.
Runs the linear static COMBINED validation pipeline for ONE case folder.

Called by:
    abaqus cae noGUI=RUN_STATIC_COMBINED_PIPELINE_omega.py -- <CASE_DIR>
"""
from __future__ import print_function
import os
import sys
import traceback

# Static scripts are kept here
STATIC_SCRIPT_DIR = r"C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts\static_scripts"

# Existing Omega Abaqus preparation scripts are kept here
BASE_SCRIPT_DIR = r"C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts"

PIPELINE_SCRIPTS = [
    (BASE_SCRIPT_DIR,   "00_import_parts_makeprecise_assemble3_omega.py"),
    (BASE_SCRIPT_DIR,   "Mesh_testing2_omega.py"),
    (BASE_SCRIPT_DIR,   "Creating_Sets5_OMEGA_MESHBASED.py"),
    (STATIC_SCRIPT_DIR, "04_static_combined_validation_omega.py"),
    (STATIC_SCRIPT_DIR, "05_static_combined_job_submit_omega.py"),
    (STATIC_SCRIPT_DIR, "06_static_combined_postprocess_omega.py"),
]


def _get_case_dir_from_argv():
    args = list(sys.argv)
    if "--" in args:
        idx = args.index("--")
        args = args[idx + 1:]

    for a in reversed(args):
        if os.path.isdir(a):
            return os.path.normpath(a)

    if args:
        return os.path.normpath(args[-1])

    raise RuntimeError(
        "CASE_DIR argument missing. Usage: "
        "abaqus cae noGUI=RUN_STATIC_COMBINED_PIPELINE_omega.py -- <CASE_DIR>"
    )


def _exec_script(path, global_ns):
    print("\n" + "=" * 90)
    print("RUNNING STATIC VALIDATION SCRIPT:")
    print(path)
    print("=" * 90)

    if not os.path.isfile(path):
        raise RuntimeError("Required script not found: %s" % path)

    execfile(path, global_ns)


def main():
    global CASE_DIR

    CASE_DIR = _get_case_dir_from_argv()

    if not os.path.isdir(CASE_DIR):
        raise RuntimeError("CASE_DIR does not exist: %s" % CASE_DIR)

    os.chdir(CASE_DIR)

    print("\nSTATIC COMBINED VALIDATION PIPELINE")
    print("CASE_DIR          :", CASE_DIR)
    print("STATIC_SCRIPT_DIR :", STATIC_SCRIPT_DIR)
    print("BASE_SCRIPT_DIR   :", BASE_SCRIPT_DIR)

    g = globals()
    g["CASE_DIR"] = CASE_DIR
    g["STATIC_SCRIPT_DIR"] = STATIC_SCRIPT_DIR
    g["BASE_SCRIPT_DIR"] = BASE_SCRIPT_DIR

    for folder, script_name in PIPELINE_SCRIPTS:
        _exec_script(os.path.join(folder, script_name), g)

    print("\nDONE: static combined validation pipeline")
    print("CASE_DIR:", CASE_DIR)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nSTATIC COMBINED VALIDATION PIPELINE FAILED")
        traceback.print_exc()
        raise
