# -*- coding: utf-8 -*-
"""
01_select_best_static_cases_from_ga.py

Standalone Python 3 helper.
Reads the latest Omega GA CSV, selects the best successful cases, and writes
selected_static_cases.json.

Usage examples:
    python 01_select_best_static_cases_from_ga.py
    python 01_select_best_static_cases_from_ga.py --csv "C:\\...\\ga_master_log_....csv" --top 3
"""
from __future__ import print_function
import os
import csv
import json
import glob
import argparse
import time

DEFAULT_GA_RESULTS_DIR = r"C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts\GA_omega_results\GAomega_result_for_m0.6_L0.4_coords10"
DEFAULT_OUTPUT_JSON = r"C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts\GA_omega_results\GAomega_result_for_m0.6_L0.4_coords10\static_results\selected_static_cases.json"


def _as_bool(x):
    return str(x).strip().lower() in ("1", "true", "yes", "y")


def _as_float(x, default=None):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def find_latest_ga_csv(results_dir):
    pattern = os.path.join(results_dir, "ga_master_log_*.csv")
    files = glob.glob(pattern)
    if not files:
        raise RuntimeError("No GA CSV found with pattern: %s" % pattern)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


def select_best_cases(csv_path, top_n=4, fitness_col="fitness_paper"):
    if not os.path.isfile(csv_path):
        raise RuntimeError("GA CSV not found: %s" % csv_path)

    rows = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("row_type", "") != "evaluation":
                continue
            if not _as_bool(row.get("success", "")):
                continue
            case_dir = row.get("case_dir", "").strip()
            if not case_dir or not os.path.isdir(case_dir):
                continue
            fitness = _as_float(row.get(fitness_col), default=None)
            if fitness is None:
                fitness = _as_float(row.get("fitness"), default=None)
            if fitness is None:
                continue
            rows.append(row)

    if not rows:
        raise RuntimeError("No successful evaluation rows with valid case_dir/fitness were found in: %s" % csv_path)

    rows.sort(key=lambda r: _as_float(r.get(fitness_col), _as_float(r.get("fitness"), 1.0e99)))

    selected = []
    seen_case_dirs = set()
    for r in rows:
        case_dir = os.path.normpath(r.get("case_dir", "").strip())
        if case_dir in seen_case_dirs:
            continue
        seen_case_dirs.add(case_dir)
        selected.append({
            "rank": len(selected) + 1,
            "case_dir": case_dir,
            "case_name": os.path.basename(case_dir),
            "fitness": _as_float(r.get("fitness"), None),
            "fitness_paper": _as_float(r.get("fitness_paper"), None),
            "fitness_lambda_over_mass": _as_float(r.get("fitness_lambda_over_mass"), None),
            "mass": _as_float(r.get("mass"), None),
            "lambda_1": _as_float(r.get("lambda_1"), None),
            "lambda_first_positive_combined": _as_float(r.get("lambda_first_positive_combined"), None),
            "stage_name": r.get("stage_name"),
            "baseline_id": r.get("baseline_id"),
            "generation": r.get("generation"),
            "index_in_generation": r.get("index_in_generation"),
            "source_csv": os.path.normpath(csv_path),
        })
        if len(selected) >= int(top_n):
            break

    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", dest="csv_path", default=None, help="Path to GA master CSV. If omitted, latest CSV is used.")
    ap.add_argument("--results-dir", default=DEFAULT_GA_RESULTS_DIR, help="Folder containing GA CSV logs.")
    ap.add_argument("--top", type=int, default=3, help="Number of successful best cases to select.")
    ap.add_argument("--out", default=DEFAULT_OUTPUT_JSON, help="Output selected_static_cases.json path.")
    args = ap.parse_args()

    csv_path = args.csv_path or find_latest_ga_csv(args.results_dir)
    selected = select_best_cases(csv_path, top_n=args.top)

    payload = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_csv": os.path.normpath(csv_path),
        "top_n": int(args.top),
        "selected_cases": selected,
    }

    out_path = os.path.normpath(args.out)
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    with open(out_path, "w") as f:
        json.dump(payload, f, indent=4, sort_keys=True)

    print("Selected %d cases from:" % len(selected))
    print(csv_path)
    print("\nWrote:")
    print(out_path)
    print("\nSelected cases:")
    for item in selected:
        print("#%d fitness_paper=%s lambda_fp_combined=%s case=%s" % (
            item["rank"], item.get("fitness_paper"), item.get("lambda_first_positive_combined"), item["case_name"]
        ))


if __name__ == "__main__":
    main()
