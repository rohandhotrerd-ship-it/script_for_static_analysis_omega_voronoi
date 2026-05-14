# -*- coding: mbcs -*-
# Abaqus/CAE Python 2.7
"""
05_static_combined_job_submit_omega.py

Submits the linear static combined validation job.
Outputs are written to:
    <CASE_DIR>\Results_Static_Combined
"""
from abaqus import mdb
from abaqusConstants import *
import os
import shutil

MODEL_NAME = "Model-Static-Combined"
JOB_NAME = "Static_Combined"
RESULTS_DIR_NAME = "Results_Static_Combined"


def _require(cond, msg):
    if not cond:
        raise RuntimeError(msg)


def _copy_if_exists(src, dst_dir):
    try:
        if os.path.isfile(src):
            dst = os.path.join(dst_dir, os.path.basename(src))
            if os.path.normcase(os.path.abspath(src)) != os.path.normcase(os.path.abspath(dst)):
                shutil.copy2(src, dst)
    except Exception as e:
        print("WARNING: copy failed:", src, str(e))


def main():
    _require('CASE_DIR' in globals() and CASE_DIR, "CASE_DIR global variable missing.")
    case_dir = os.path.normpath(CASE_DIR)
    _require(os.path.isdir(case_dir), "CASE_DIR not found: %s" % case_dir)

    results_dir = os.path.join(case_dir, RESULTS_DIR_NAME)
    if not os.path.isdir(results_dir):
        os.makedirs(results_dir)

    _require(MODEL_NAME in mdb.models.keys(), "Model not found: %s" % MODEL_NAME)

    old_cwd = os.getcwd()
    os.chdir(results_dir)
    print("Static combined results dir:", results_dir)

    if JOB_NAME in mdb.jobs.keys():
        del mdb.jobs[JOB_NAME]

    job = mdb.Job(
        name=JOB_NAME,
        model=MODEL_NAME,
        description="Linear static combined validation for selected Omega GA design",
        type=ANALYSIS,
        atTime=None,
        waitMinutes=0,
        waitHours=0,
        queue=None,
        memory=90,
        memoryUnits=PERCENTAGE,
        getMemoryFromAnalysis=True,
        explicitPrecision=SINGLE,
        nodalOutputPrecision=SINGLE,
        echoPrint=OFF,
        modelPrint=OFF,
        contactPrint=OFF,
        historyPrint=OFF,
        userSubroutine='',
        scratch='',
        resultsFormat=ODB,
        multiprocessingMode=DEFAULT,
        numCpus=1,
        numDomains=1,
        numGPUs=0,
    )

    print("Writing static combined input...")
    job.writeInput(consistencyChecking=OFF)

    print("Submitting static combined job...")
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()

    # Save CAE database for manual inspection/debugging.
    try:
        cae_path = os.path.join(results_dir, "Static_Combined_Setup.cae")
        mdb.saveAs(pathName=cae_path)
        print("Saved CAE:", cae_path)
    except Exception as e:
        print("WARNING: Could not save CAE:", str(e))

    # Basic existence check.
    odb_path = os.path.join(results_dir, JOB_NAME + ".odb")
    if not os.path.isfile(odb_path):
        raise RuntimeError("Static combined ODB not found after job completion: %s" % odb_path)

    os.chdir(old_cwd)
    print("\nDONE: 05_static_combined_job_submit_omega.py")
    print("ODB:", odb_path)


if __name__ == "__main__":
    main()
