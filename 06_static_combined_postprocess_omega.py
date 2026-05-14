# -*- coding: mbcs -*-
# Abaqus Python 2.7
"""
06_static_combined_postprocess_omega.py

Postprocesses Static_Combined.odb and writes numerical mentor checks:
- max U magnitude
- max absolute U1, U2, U3
- S11/S22/S33 min/max
- max absolute S33
- max von Mises

No images are generated. Open the ODB manually for contour screenshots.
"""
from odbAccess import openOdb
import os
import json
import csv
import math

JOB_NAME = "Static_Combined"
STEP_NAME = "Static_Combined_Step"
RESULTS_DIR_NAME = "Results_Static_Combined"
SUMMARY_JSON = "static_combined_summary.json"
SUMMARY_CSV = "static_combined_summary.csv"


def _require(cond, msg):
    if not cond:
        raise RuntimeError(msg)


def _mag(vec):
    return math.sqrt(sum([float(x) * float(x) for x in vec]))


def _init_minmax():
    return {"min": None, "max": None}


def _update_minmax(mm, v):
    if v is None:
        return
    v = float(v)
    if mm["min"] is None or v < mm["min"]:
        mm["min"] = v
    if mm["max"] is None or v > mm["max"]:
        mm["max"] = v


def _get_component(data, idx):
    try:
        if len(data) > idx:
            return float(data[idx])
    except:
        pass
    return None



def _safe_instance_name(value):
    try:
        inst = getattr(value, "instance", None)
        if inst is not None:
            nm = getattr(inst, "name", None)
            if nm:
                return str(nm)
    except:
        pass
    return "ASSEMBLY_OR_UNKNOWN"


def _safe_label(value, preferred="node"):
    # Some Abaqus field values do not have instance/node/element labels,
    # especially assembly-level or RP values. Keep postprocessing robust.
    if preferred == "node":
        for attr in ["nodeLabel", "elementLabel", "integrationPoint"]:
            try:
                vv = getattr(value, attr, None)
                if vv is not None:
                    return str(vv)
            except:
                pass
    else:
        for attr in ["elementLabel", "nodeLabel", "integrationPoint"]:
            try:
                vv = getattr(value, attr, None)
                if vv is not None:
                    return str(vv)
            except:
                pass
    return "NA"


def main():
    _require('CASE_DIR' in globals() and CASE_DIR, "CASE_DIR global variable missing.")
    case_dir = os.path.normpath(CASE_DIR)
    results_dir = os.path.join(case_dir, RESULTS_DIR_NAME)
    odb_path = os.path.join(results_dir, JOB_NAME + ".odb")

    _require(os.path.isfile(odb_path), "ODB not found: %s" % odb_path)

    odb = openOdb(path=odb_path, readOnly=True)
    try:
        _require(STEP_NAME in odb.steps.keys(), "Step not found in ODB: %s" % STEP_NAME)
        step = odb.steps[STEP_NAME]
        _require(len(step.frames) > 0, "No frames in step: %s" % STEP_NAME)
        frame = step.frames[-1]

        summary = {
            "case_dir": case_dir,
            "case_name": os.path.basename(case_dir),
            "results_dir": results_dir,
            "odb_path": odb_path,
            "step_name": STEP_NAME,
            "frame_id": len(step.frames) - 1,
        }

        # ---------------- Displacement U ----------------
        if "U" in frame.fieldOutputs.keys():
            u_field = frame.fieldOutputs["U"]
            max_u_mag = None
            max_u_label = None
            max_abs_u1 = 0.0
            max_abs_u2 = 0.0
            max_abs_u3 = 0.0
            max_abs_u3_label = None

            for v in u_field.values:
                data = v.data
                u1 = _get_component(data, 0) or 0.0
                u2 = _get_component(data, 1) or 0.0
                u3 = _get_component(data, 2) or 0.0
                umag = _mag([u1, u2, u3])
                if max_u_mag is None or umag > max_u_mag:
                    max_u_mag = umag
                    max_u_label = "%s:%s" % (_safe_instance_name(v), _safe_label(v, "node"))
                if abs(u1) > max_abs_u1:
                    max_abs_u1 = abs(u1)
                if abs(u2) > max_abs_u2:
                    max_abs_u2 = abs(u2)
                if abs(u3) > max_abs_u3:
                    max_abs_u3 = abs(u3)
                    max_abs_u3_label = "%s:%s" % (_safe_instance_name(v), _safe_label(v, "node"))

            summary.update({
                "max_U_mag": max_u_mag,
                "max_U_node": max_u_label,
                "max_abs_U1": max_abs_u1,
                "max_abs_U2": max_abs_u2,
                "max_abs_U3": max_abs_u3,
                "max_abs_U3_node": max_abs_u3_label,
            })
        else:
            summary["warning_U"] = "U field output not found."

        # ---------------- Stress S ----------------
        if "S" in frame.fieldOutputs.keys():
            s_field = frame.fieldOutputs["S"]
            s11 = _init_minmax()
            s22 = _init_minmax()
            s33 = _init_minmax()
            s12 = _init_minmax()
            max_abs_s33 = 0.0
            max_mises = None
            max_mises_label = None

            for v in s_field.values:
                data = v.data
                v_s11 = _get_component(data, 0)
                v_s22 = _get_component(data, 1)
                v_s33 = _get_component(data, 2)
                v_s12 = _get_component(data, 3)

                _update_minmax(s11, v_s11)
                _update_minmax(s22, v_s22)
                _update_minmax(s33, v_s33)
                _update_minmax(s12, v_s12)

                if v_s33 is not None and abs(v_s33) > max_abs_s33:
                    max_abs_s33 = abs(v_s33)

                try:
                    mises = float(v.mises)
                    if max_mises is None or mises > max_mises:
                        max_mises = mises
                        # elementLabel may not exist for all output positions
                        label = getattr(v, "elementLabel", None)
                        max_mises_label = "%s:%s" % (_safe_instance_name(v), _safe_label(v, "element"))
                except:
                    pass

            summary.update({
                "S11_min": s11["min"], "S11_max": s11["max"],
                "S22_min": s22["min"], "S22_max": s22["max"],
                "S33_min": s33["min"], "S33_max": s33["max"],
                "S12_min": s12["min"], "S12_max": s12["max"],
                "max_abs_S33": max_abs_s33,
                "max_mises": max_mises,
                "max_mises_location": max_mises_label,
            })
        else:
            summary["warning_S"] = "S field output not found."

        summary["status"] = "OK"

    finally:
        odb.close()

    json_path = os.path.join(results_dir, SUMMARY_JSON)
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=4, sort_keys=True)

    csv_path = os.path.join(results_dir, SUMMARY_CSV)
    fields = [
        "case_name", "status", "max_U_mag", "max_abs_U1", "max_abs_U2", "max_abs_U3",
        "S11_min", "S11_max", "S22_min", "S22_max", "S33_min", "S33_max", "max_abs_S33",
        "S12_min", "S12_max", "max_mises", "max_U_node", "max_abs_U3_node", "max_mises_location",
        "odb_path",
    ]
    with open(csv_path, "w") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerow(summary)

    print("\nDONE: 06_static_combined_postprocess_omega.py")
    print("Summary JSON:", json_path)
    print("Summary CSV :", csv_path)


if __name__ == "__main__":
    main()
