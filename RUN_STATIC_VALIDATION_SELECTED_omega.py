# -*- coding: utf-8 -*-
"""
RUN_STATIC_VALIDATION_SELECTED_omega.py

Python 3 runner to validate the best Omega GA designs using a linear static
COMBINED load case.
"""
from __future__ import print_function
import os
import csv
import json
import glob
import time
import argparse
import subprocess

# ---------------- USER PATHS ----------------
ABAQUS_BAT = r"C:\SIMULIA\abaqus\Commands\abaqus.bat"

SCRIPT_DIR = r"C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts\static_scripts"

GA_RESULTS_DIR = r"C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts\GA_omega_results\GAomega_result_for_m0.6_L0.4_coords10"

STATIC_RESULTS_DIR = r"C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts\GA_omega_results\GAomega_result_for_m0.6_L0.4_coords10\static_results"

STATIC_PIPELINE_SCRIPT = os.path.join(SCRIPT_DIR, "RUN_STATIC_COMBINED_PIPELINE_omega.py")

SELECTED_JSON = os.path.join(STATIC_RESULTS_DIR, "selected_static_cases.json")
FINAL_SUMMARY_JSON = os.path.join(STATIC_RESULTS_DIR, "static_validation_selected_summary.json")
FINAL_SUMMARY_CSV = os.path.join(STATIC_RESULTS_DIR, "static_validation_selected_summary.csv")


def _as_bool(x):
    return str(x).strip().lower() in ("1", "true", "yes", "y")


def _as_float(x, default=None):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def _ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def _safe_output_path(path):
    """
    If the target CSV/JSON is open in Excel/Abaqus/PyCharm and Windows blocks
    overwrite, write a timestamped fallback file instead of crashing.
    """
    folder = os.path.dirname(path)
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, "%s_%s%s" % (name, stamp, ext))


def find_latest_ga_csv(results_dir):
    files = glob.glob(os.path.join(results_dir, "ga_master_log_*.csv"))
    if not files:
        raise RuntimeError("No GA CSV found in: %s" % results_dir)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


def select_best_cases(csv_path, top_n):
    rows = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("row_type") != "evaluation":
                continue
            if not _as_bool(row.get("success")):
                continue
            case_dir = row.get("case_dir", "").strip()
            if not case_dir or not os.path.isdir(case_dir):
                continue
            fitness = _as_float(row.get("fitness_paper"), _as_float(row.get("fitness"), None))
            if fitness is None:
                continue
            rows.append(row)

    if not rows:
        raise RuntimeError("No successful GA cases found in: %s" % csv_path)

    rows.sort(key=lambda r: _as_float(r.get("fitness_paper"), _as_float(r.get("fitness"), 1.0e99)))

    selected = []
    seen = set()
    for row in rows:
        case_dir = os.path.normpath(row.get("case_dir"))
        if case_dir in seen:
            continue
        seen.add(case_dir)
        selected.append({
            "rank": len(selected) + 1,
            "case_dir": case_dir,
            "case_name": os.path.basename(case_dir),
            "fitness_paper": _as_float(row.get("fitness_paper")),
            "fitness_lambda_over_mass": _as_float(row.get("fitness_lambda_over_mass")),
            "fitness": _as_float(row.get("fitness")),
            "mass": _as_float(row.get("mass")),
            "lambda_1": _as_float(row.get("lambda_1")),
            "lambda_first_positive_combined": _as_float(row.get("lambda_first_positive_combined")),
            "stage_name": row.get("stage_name"),
            "baseline_id": row.get("baseline_id"),
            "generation": row.get("generation"),
            "index_in_generation": row.get("index_in_generation"),
            "source_csv": os.path.normpath(csv_path),
        })
        if len(selected) >= int(top_n):
            break
    return selected


def write_selected_json(selected, csv_path, top_n):
    _ensure_dir(STATIC_RESULTS_DIR)
    payload = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_csv": os.path.normpath(csv_path),
        "top_n": int(top_n),
        "selected_cases": selected,
    }
    with open(SELECTED_JSON, "w") as f:
        json.dump(payload, f, indent=4, sort_keys=True)
    return SELECTED_JSON


def run_static_pipeline(case_item):
    case_dir = case_item["case_dir"]
    static_dir = os.path.join(case_dir, "Results_Static_Combined")
    _ensure_dir(static_dir)

    stdout_log = os.path.join(static_dir, "validation_runner_stdout.txt")
    stderr_log = os.path.join(static_dir, "validation_runner_stderr.txt")

    cmd = [
        ABAQUS_BAT,
        "cae",
        "noGUI=%s" % STATIC_PIPELINE_SCRIPT,
        "--",
        case_dir,
    ]

    print("\n" + "=" * 90)
    print("STATIC COMBINED VALIDATION | rank %s" % case_item.get("rank"))
    print("Case:", case_item.get("case_name"))
    print("Case dir:", case_dir)
    print("Command:")
    print(" ".join(['\"%s\"' % c if ' ' in c else c for c in cmd]))

    t0 = time.time()
    p = subprocess.run(
        cmd,
        check=False,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    elapsed = time.time() - t0

    with open(stdout_log, "w") as f:
        f.write(p.stdout or "")
    with open(stderr_log, "w") as f:
        f.write(p.stderr or "")

    summary_path = os.path.join(static_dir, "static_combined_summary.json")
    summary = None
    if os.path.isfile(summary_path):
        try:
            with open(summary_path, "r") as f:
                summary = json.load(f)
        except Exception as e:
            summary = {"postprocess_read_error": str(e)}

    result = dict(case_item)
    result.update({
        "static_validation_success": p.returncode == 0 and summary is not None,
        "returncode": p.returncode,
        "elapsed_sec": elapsed,
        "static_results_dir": static_dir,
        "static_summary_json": summary_path if os.path.isfile(summary_path) else None,
        "stdout_log": stdout_log,
        "stderr_log": stderr_log,
    })

    if isinstance(summary, dict):
        result.update(summary)

    print("Return code:", p.returncode)
    print("Elapsed sec:", elapsed)
    print("Summary JSON:", result.get("static_summary_json"))

    if p.returncode != 0:
        print("STDOUT tail:")
        print("\n".join((p.stdout or "").splitlines()[-20:]))
        print("STDERR tail:")
        print("\n".join((p.stderr or "").splitlines()[-20:]))

    return result


def write_final_summary(results):
    _ensure_dir(STATIC_RESULTS_DIR)

    payload = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
    }

    json_path = FINAL_SUMMARY_JSON
    try:
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=4, sort_keys=True)
    except PermissionError:
        json_path = _safe_output_path(FINAL_SUMMARY_JSON)
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=4, sort_keys=True)

    fields = [
        "rank", "case_name", "case_dir", "static_validation_success", "returncode",
        "fitness_paper", "mass", "lambda_first_positive_combined",
        "max_U_mag", "max_abs_U1", "max_abs_U2", "max_abs_U3",
        "S11_min", "S11_max", "S22_min", "S22_max", "S33_min", "S33_max", "max_abs_S33",
        "max_mises", "static_results_dir", "static_summary_json", "elapsed_sec",
    ]

    csv_path = FINAL_SUMMARY_CSV
    try:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in results:
                w.writerow(r)
    except PermissionError:
        csv_path = _safe_output_path(FINAL_SUMMARY_CSV)
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in results:
                w.writerow(r)

    print("\n" + "=" * 90)
    print("STATIC VALIDATION FINISHED")
    print("Summary JSON:", json_path)
    print("Summary CSV :", csv_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None, help="GA master CSV. If omitted, latest CSV is used.")
    ap.add_argument("--top", type=int, default=3, help="Number of best successful GA cases to validate.")
    args = ap.parse_args()

    if not os.path.isfile(ABAQUS_BAT):
        raise RuntimeError("Abaqus bat not found: %s" % ABAQUS_BAT)
    if not os.path.isfile(STATIC_PIPELINE_SCRIPT):
        raise RuntimeError("Static pipeline script not found: %s" % STATIC_PIPELINE_SCRIPT)

    csv_path = args.csv or find_latest_ga_csv(GA_RESULTS_DIR)
    selected = select_best_cases(csv_path, args.top)
    selected_path = write_selected_json(selected, csv_path, args.top)

    print("Selected cases JSON:", selected_path)
    for item in selected:
        print("#%s fitness_paper=%s case=%s" % (item["rank"], item.get("fitness_paper"), item.get("case_name")))

    results = []
    for item in selected:
        results.append(run_static_pipeline(item))

    write_final_summary(results)


if __name__ == "__main__":
    main()
