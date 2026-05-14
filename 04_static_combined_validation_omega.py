# -*- coding: mbcs -*-
# Abaqus/CAE Python 2.7
"""
04_static_combined_validation_omega.py

Creates a LINEAR STATIC COMBINED validation model for the Omega workflow.

Purpose:
- Use same parts, material, sections, ties, BCs and combined load directions
  as the working buckling setup.
- Replace BuckleStep with StaticStep(nlgeom=OFF).
- Request field outputs needed for mentor checks: U, S, RF.

Expected previous scripts:
- 00_import_parts_makeprecise_assemble3_omega.py
- Mesh_testing2_omega.py
- Creating_Sets5_OMEGA_MESHBASED.py

Output model:
- Model-Static-Combined
"""
from abaqus import mdb
from abaqusConstants import *
from interaction import *
from load import *
from step import *
import os
import json

# ============================================================
# USER SETTINGS
# ============================================================
BASE_MODEL = "Model-1"
MODEL_STATIC_COMBINED = "Model-Static-Combined"

PARTS = ["S_full", "S_half_patches", "Lower_Skin"]
INST_SFULL          = "S_full-1"
INST_SHALF_PATCHES = "S_half_patches-1"
INST_LOWERSKIN      = "Lower_Skin-1"

MAT_NAME = "Aluminium_2024_T3"
SEC_NAME_SKIN = "Shell_Lower_Skin"
SEC_NAME_STIFF = "Shell_Stiffeners"
DEFAULT_THICKNESS_SKIN = 3.0
DEFAULT_THICKNESS_STIFF = 3.0

DENSITY = 2.78e-9
E = 73100.0
NU = 0.33
PLASTIC_TABLE = ((345.0, 0.0), (483.0, 0.15))

STEP_NAME = "Static_Combined_Step"

SET_LOWER_LEFT   = "SET_LOWERSKIN_EDGE_LEFT"
SET_LOWER_RIGHT  = "SET_LOWERSKIN_EDGE_RIGHT"
SET_LOWER_TOP    = "SET_LOWERSKIN_EDGE_TOP"
SET_LOWER_BOTTOM = "SET_LOWERSKIN_EDGE_BOTTOM"

SET_SFULL_LEFT   = "SET_SFULL_BOUNDARY_EDGE_LEFT"
SET_SFULL_RIGHT  = "SET_SFULL_BOUNDARY_EDGE_RIGHT"
SET_SFULL_TOP    = "SET_SFULL_BOUNDARY_EDGE_TOP"
SET_SFULL_BOTTOM = "SET_SFULL_BOUNDARY_EDGE_BOTTOM"

SURF_LOAD_LEFT   = "SURF_EDGES__SET_LOWERSKIN_EDGE_LEFT"
SURF_LOAD_RIGHT  = "SURF_EDGES__SET_LOWERSKIN_EDGE_RIGHT"
SURF_LOAD_TOP    = "SURF_EDGES__SET_LOWERSKIN_EDGE_TOP"
SURF_LOAD_BOT    = "SURF_EDGES__SET_LOWERSKIN_EDGE_BOTTOM"

RP_SET_LEFT      = "SET_RP_LEFT"
RP_SET_RIGHT     = "SET_RP_RIGHT"
RP_SET_SHEAR_TOP = "SET_RP_SHEAR_TOP"
RP_SET_SHEAR_BOT = "SET_RP_SHEAR_BOTTOM"

COUPLING_LEFT      = "Coupling_Left"
COUPLING_RIGHT     = "Coupling_Right"
COUPLING_SHEAR_TOP = "Coupling_Shear_Top"
COUPLING_SHEAR_BOT = "Coupling_Shear_Bottom"

SET_CORNER_A = "SET_CORNER_A_BOTTOM_LEFT"
SET_CORNER_B = "SET_CORNER_B_TOP_LEFT"
SET_CORNER_C = "SET_CORNER_C_BOTTOM_RIGHT"

RP_OFFSET_MM = 20.0
COMP_LINE_LOAD_N_PER_MM  = 16.0
SHEAR_LINE_LOAD_N_PER_MM = 86.0

LOAD_COMB_LEFT_NAME        = "Load_Combined_Compression_Left"
LOAD_COMB_RIGHT_NAME       = "Load_Combined_Compression_Right"
LOAD_COMB_SHEAR_LEFT_NAME  = "Load_Combined_Shear_Left"
LOAD_COMB_SHEAR_RIGHT_NAME = "Load_Combined_Shear_Right"
LOAD_COMB_TOP_NAME         = "Load_Combined_Shear_Top"
LOAD_COMB_BOT_NAME         = "Load_Combined_Shear_Bottom"

OLD_LOAD_NAMES = [
    "Load-1", "Load_Compression", "Load_Shear", "Load_Combined",
    "Load_Compression_Left", "Load_Compression_Right",
    "Load_Shear_Left", "Load_Shear_Right", "Load_Shear_Top", "Load_Shear_Bottom",
    LOAD_COMB_LEFT_NAME, LOAD_COMB_RIGHT_NAME, LOAD_COMB_SHEAR_LEFT_NAME,
    LOAD_COMB_SHEAR_RIGHT_NAME, LOAD_COMB_TOP_NAME, LOAD_COMB_BOT_NAME,
]

OLD_BC_NAMES = [
    "Lower_Skin_bot_edge", "Sfull_endbot_edges", "LowerSkin_top", "Sfull_endtop",
    "LowerSkin_right", "Sfull_endright", "LowerSkin_left", "Sfull_endleft",
    "BC_SS_LowerSkin_Left", "BC_SS_LowerSkin_Right", "BC_SS_Sfull_Left", "BC_SS_Sfull_Right",
    "BC_CLAMP_LowerSkin_Left", "BC_CLAMP_Sfull_Left", "BC_SS_LowerSkin_Top", "BC_SS_Sfull_Top",
    "BC_SS_LowerSkin_Bottom", "BC_SS_Sfull_Bottom", "BC_Bottom_LowerSkin", "BC_Bottom_Sfull",
    "BC_Bottom_U1_LowerSkin", "BC_Bottom_U1_Sfull", "BC_Bottom_U2_LowerSkin", "BC_Bottom_U2_Sfull",
    "BC_Stab_Corner_U1", "BC_Stab_Corner_U2", "BC_CORNER_A", "BC_CORNER_B", "BC_CORNER_C",
]

OLD_CONSTRAINT_NAMES = [
    "Coupling_LoadEdge", COUPLING_LEFT, COUPLING_RIGHT, COUPLING_SHEAR_TOP, COUPLING_SHEAR_BOT,
]

OLD_SET_NAMES = ["SET_RP_LOAD", RP_SET_LEFT, RP_SET_RIGHT, RP_SET_SHEAR_TOP, RP_SET_SHEAR_BOT,
                 SET_CORNER_A, SET_CORNER_B, SET_CORNER_C]

TIES = [
    ("Lower_skin_Sfull",
     ("ASM", "SURF_LOWERSKIN_TOP_SPOS"),
     ("ASM", "SURF_SFULL_BOT_FLANGE_SNEG")),
    ("Lower_skin_ShalfS_half_patches",
     ("ASM", "SURF_SHALF_PATCHES_LOWER_SNEG"),
     ("ASM", "SURF_LOWERSKIN_TOP_SPOS")),
    ("Sfull_ShalfS_half_patches",
     (INST_SFULL, "SURF_SFULL_SHALF_PATCH_IFACE_MESH_S1"),
     (INST_SHALF_PATCHES, "SURF_SHALF_PATCHES_SFULL_IFACE_MESH_S1")),
]
# ============================================================


def _require(cond, msg):
    if not cond:
        raise RuntimeError(msg)


def _safe_del(obj_dict, key):
    try:
        if key in obj_dict.keys():
            del obj_dict[key]
    except:
        pass


def _safe_del_tie(model, tie_name):
    if hasattr(model, "constraints"):
        _safe_del(model.constraints, tie_name)
    if hasattr(model, "interactions"):
        _safe_del(model.interactions, tie_name)


def _safe_del_load(model, load_name):
    try:
        if load_name in model.loads.keys():
            del model.loads[load_name]
    except:
        pass


def _safe_del_bc(model, bc_name):
    try:
        if bc_name in model.boundaryConditions.keys():
            del model.boundaryConditions[bc_name]
    except:
        pass


def _safe_del_constraint(model, name):
    try:
        if hasattr(model, "constraints") and name in model.constraints.keys():
            del model.constraints[name]
    except:
        pass


def _safe_del_asm_set(asm, name):
    try:
        if name in asm.sets.keys():
            del asm.sets[name]
    except:
        pass


def _get_model(model_name):
    _require(model_name in mdb.models.keys(), "Model '%s' not found." % model_name)
    return mdb.models[model_name]


def _get_asm(model):
    return model.rootAssembly


def _get_region_from_surface(model, surf_ref):
    """
    Resolve a surface reference.

    Supported formats:
      ("ASM", "SURFACE_NAME")
      ("INSTANCE_NAME", "SURFACE_NAME")
      ("ASM_OPTIONAL", "PREFERRED_SURFACE", "FALLBACK_SURFACE")

    ASM_OPTIONAL is used for the local lower-skin contact surfaces:
    if the preferred local surface was not created, the script falls back
    to the old broad lower-skin top surface.
    """
    asm = _get_asm(model)

    _require(isinstance(surf_ref, tuple) and len(surf_ref) >= 2,
             "Invalid surface reference: %s" % str(surf_ref))

    scope = surf_ref[0]

    if scope == "ASM":
        name = surf_ref[1]
        _require(name in asm.surfaces.keys(), "Assembly surface not found: %s" % name)
        return asm.surfaces[name]

    if scope == "ASM_OPTIONAL":
        _require(len(surf_ref) >= 3, "ASM_OPTIONAL needs preferred and fallback surface names.")
        preferred = surf_ref[1]
        fallback = surf_ref[2]

        if preferred in asm.surfaces.keys():
            print("Using preferred local assembly surface:", preferred)
            return asm.surfaces[preferred]

        print("WARNING: preferred local surface not found:", preferred)
        print("WARNING: falling back to assembly surface:", fallback)

        _require(fallback in asm.surfaces.keys(), "Fallback assembly surface not found: %s" % fallback)
        return asm.surfaces[fallback]

    name = surf_ref[1]
    _require(scope in asm.instances.keys(), "Instance not found: %s" % scope)
    inst = asm.instances[scope]
    _require(name in inst.surfaces.keys(), "Instance surface not found: %s.%s" % (scope, name))
    return inst.surfaces[name]

def _get_region_from_set(model, set_name):
    asm = _get_asm(model)
    _require(set_name in asm.sets.keys(), "Assembly set not found: %s" % set_name)
    return asm.sets[set_name]


def _edge_length(edge):
    try:
        return float(edge.getSize(printResults=False))
    except:
        pass
    try:
        return float(edge.getSize(False))
    except:
        pass
    raise RuntimeError("Could not evaluate edge length.")


def _sum_edge_set_length_mm(model, set_name):
    asm = _get_asm(model)
    _require(set_name in asm.sets.keys(), "Assembly set not found: %s" % set_name)
    s = asm.sets[set_name]
    edges = s.edges
    _require(edges is not None and len(edges) > 0, "Set '%s' does not contain edges." % set_name)
    total = 0.0
    for e in edges:
        total += _edge_length(e)
    return total


def _bbox_of_edge_set(model, set_name):
    asm = _get_asm(model)
    _require(set_name in asm.sets.keys(), "Assembly set not found: %s" % set_name)
    s = asm.sets[set_name]
    edges = s.edges
    _require(edges is not None and len(edges) > 0, "Set '%s' does not contain edges." % set_name)
    bb = edges.getBoundingBox()
    return bb['low'], bb['high']


def _outside_rp_point_from_set(model, set_name, direction):
    low, high = _bbox_of_edge_set(model, set_name)
    x_mid = 0.5 * (low[0] + high[0])
    y_mid = 0.5 * (low[1] + high[1])
    z_mid = 0.5 * (low[2] + high[2])
    if direction == "left":
        return (low[0] - RP_OFFSET_MM, y_mid, z_mid)
    if direction == "right":
        return (high[0] + RP_OFFSET_MM, y_mid, z_mid)
    if direction == "top":
        return (x_mid, high[1] + RP_OFFSET_MM, z_mid)
    if direction == "bottom":
        return (x_mid, low[1] - RP_OFFSET_MM, z_mid)
    raise RuntimeError("Unknown direction: %s" % direction)


def _create_rp_set_outside(model, rp_set_name, source_set_name, direction):
    asm = _get_asm(model)
    _safe_del_asm_set(asm, rp_set_name)
    rp_pt = _outside_rp_point_from_set(model, source_set_name, direction)
    feat = asm.ReferencePoint(point=rp_pt)
    rp = asm.referencePoints[feat.id]
    asm.Set(name=rp_set_name, referencePoints=(rp,))
    print("Created RP set:", rp_set_name, "at", rp_pt)


def _read_design_vars_json():
    if 'CASE_DIR' not in globals() or not CASE_DIR:
        print("WARNING: CASE_DIR not found; using default thickness.")
        return None
    design_path = os.path.join(os.path.normpath(CASE_DIR), "design_vars.json")
    if not os.path.isfile(design_path):
        print("WARNING: design_vars.json not found; using default thickness.")
        print("Expected:", design_path)
        return None
    try:
        f = open(design_path, "r")
        try:
            data = json.load(f)
        finally:
            f.close()
        print("Read design_vars.json:", design_path)
        print("Design vars:", data)
        return data
    except Exception as e:
        print("WARNING: Could not read design_vars.json; using default thickness.")
        print(str(e))
        return None


def _get_thicknesses_from_design():
    data = _read_design_vars_json()
    t_skin = DEFAULT_THICKNESS_SKIN
    t_stiff = DEFAULT_THICKNESS_STIFF
    if not isinstance(data, dict):
        return t_skin, t_stiff
    try:
        t_skin = float(data.get("Thickness_skin", data.get("Thickness", DEFAULT_THICKNESS_SKIN)))
        if t_skin <= 0.0: raise RuntimeError()
    except:
        t_skin = DEFAULT_THICKNESS_SKIN
    try:
        t_stiff = float(data.get("Thickness_stiff", data.get("Thickness", DEFAULT_THICKNESS_STIFF)))
        if t_stiff <= 0.0: raise RuntimeError()
    except:
        t_stiff = DEFAULT_THICKNESS_STIFF
    return t_skin, t_stiff


def create_material_and_sections(model, thickness_skin, thickness_stiff):
    if MAT_NAME in model.materials.keys():
        mat = model.materials[MAT_NAME]
    else:
        mat = model.Material(name=MAT_NAME)
    try: mat.Density(table=((DENSITY,),))
    except: pass
    try: mat.Elastic(table=((E, NU),))
    except: pass
    try: mat.Plastic(table=PLASTIC_TABLE)
    except: pass

    if SEC_NAME_SKIN in model.sections.keys(): _safe_del(model.sections, SEC_NAME_SKIN)
    if SEC_NAME_STIFF in model.sections.keys(): _safe_del(model.sections, SEC_NAME_STIFF)

    model.HomogeneousShellSection(name=SEC_NAME_SKIN, material=MAT_NAME, thicknessType=UNIFORM,
                                  thickness=thickness_skin, thicknessField='', idealization=NO_IDEALIZATION,
                                  poissonDefinition=DEFAULT, thicknessModulus=None, temperature=GRADIENT,
                                  useDensity=OFF, integrationRule=SIMPSON, numIntPts=5)
    model.HomogeneousShellSection(name=SEC_NAME_STIFF, material=MAT_NAME, thicknessType=UNIFORM,
                                  thickness=thickness_stiff, thicknessField='', idealization=NO_IDEALIZATION,
                                  poissonDefinition=DEFAULT, thicknessModulus=None, temperature=GRADIENT,
                                  useDensity=OFF, integrationRule=SIMPSON, numIntPts=5)
    print("Created/updated sections. t_skin=", thickness_skin, "t_stiff=", thickness_stiff)


def assign_section_to_all_parts(model):
    for p_name in PARTS:
        _require(p_name in model.parts.keys(), "Part not found: %s" % p_name)
        p = model.parts[p_name]
        set_all = "ALL_FACES__" + p_name
        if set_all in p.sets.keys(): _safe_del(p.sets, set_all)
        p.Set(name=set_all, faces=p.faces)
        section_name = SEC_NAME_SKIN if p_name == "Lower_Skin" else SEC_NAME_STIFF
        p.SectionAssignment(region=p.sets[set_all], sectionName=section_name, offset=0.0,
                            offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
        print("Assigned section to part:", p_name, section_name)


def create_static_step(model):
    if STEP_NAME in model.steps.keys(): _safe_del(model.steps, STEP_NAME)
    model.StaticStep(name=STEP_NAME, previous='Initial', nlgeom=OFF,
                     initialInc=0.1, minInc=1e-8, maxInc=0.1, maxNumInc=100)
    # Field output for mentor checks: displacement, stresses, reactions.
    if "F-Output-1" in model.fieldOutputRequests.keys():
        model.fieldOutputRequests["F-Output-1"].setValues(variables=("S", "U", "RF"))
    else:
        model.FieldOutputRequest(name="F-Output-1", createStepName=STEP_NAME, variables=("S", "U", "RF"))
    print("Created linear static step:", STEP_NAME)


def create_ties(model):
    for tie_name, master_ref, slave_ref in TIES:
        _safe_del_tie(model, tie_name)
        master_region = _get_region_from_surface(model, master_ref)
        slave_region  = _get_region_from_surface(model, slave_ref)
        model.Tie(name=tie_name, master=master_region, slave=slave_region,
                  positionToleranceMethod=COMPUTED, adjust=ON, tieRotations=ON, thickness=ON)
        print("Created Tie:", tie_name)


def clear_old_loads_and_bcs(model):
    asm = _get_asm(model)
    for name in OLD_LOAD_NAMES: _safe_del_load(model, name)
    for name in OLD_BC_NAMES: _safe_del_bc(model, name)
    for name in OLD_CONSTRAINT_NAMES: _safe_del_constraint(model, name)
    for name in OLD_SET_NAMES: _safe_del_asm_set(asm, name)


def create_simply_supported_u3_bc(model):
    bc_specs = [
        ("BC_SS_LowerSkin_Left", SET_LOWER_LEFT),
        ("BC_SS_LowerSkin_Right", SET_LOWER_RIGHT),
        ("BC_SS_LowerSkin_Top", SET_LOWER_TOP),
        ("BC_SS_LowerSkin_Bottom", SET_LOWER_BOTTOM),
        ("BC_SS_Sfull_Left", SET_SFULL_LEFT),
        ("BC_SS_Sfull_Right", SET_SFULL_RIGHT),
        ("BC_SS_Sfull_Top", SET_SFULL_TOP),
        ("BC_SS_Sfull_Bottom", SET_SFULL_BOTTOM),
    ]
    for bc_name, set_name in bc_specs:
        region = _get_region_from_set(model, set_name)
        model.DisplacementBC(name=bc_name, createStepName='Initial', region=region,
                             u1=UNSET, u2=UNSET, u3=0.0,
                             ur1=UNSET, ur2=UNSET, ur3=UNSET,
                             amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
        print("Created U3=0 BC:", bc_name)


def _pick_closest_vertex(inst, target_xyz):
    best_idx = None
    best_d2 = None
    for i, v in enumerate(inst.vertices):
        try: p = v.pointOn[0]
        except: continue
        dx = p[0] - target_xyz[0]; dy = p[1] - target_xyz[1]; dz = p[2] - target_xyz[2]
        d2 = dx*dx + dy*dy + dz*dz
        if best_idx is None or d2 < best_d2:
            best_idx = i; best_d2 = d2
    _require(best_idx is not None, "Could not find corner vertex on %s" % INST_LOWERSKIN)
    return inst.vertices[best_idx:best_idx+1]


def create_corner_stabilization_sets(model):
    asm = _get_asm(model)
    inst = asm.instances[INST_LOWERSKIN]
    left_low, left_high = _bbox_of_edge_set(model, SET_LOWER_LEFT)
    right_low, right_high = _bbox_of_edge_set(model, SET_LOWER_RIGHT)
    top_low, top_high = _bbox_of_edge_set(model, SET_LOWER_TOP)
    bot_low, bot_high = _bbox_of_edge_set(model, SET_LOWER_BOTTOM)
    x_left = 0.5 * (left_low[0] + left_high[0])
    x_right = 0.5 * (right_low[0] + right_high[0])
    y_top = 0.5 * (top_low[1] + top_high[1])
    y_bottom = 0.5 * (bot_low[1] + bot_high[1])
    inst_bb = inst.vertices.getBoundingBox()
    z_mid = 0.5 * (inst_bb['low'][2] + inst_bb['high'][2])
    vA = _pick_closest_vertex(inst, (x_left,  y_bottom, z_mid))
    vB = _pick_closest_vertex(inst, (x_left,  y_top,    z_mid))
    vC = _pick_closest_vertex(inst, (x_right, y_bottom, z_mid))
    for s in [SET_CORNER_A, SET_CORNER_B, SET_CORNER_C]: _safe_del_asm_set(asm, s)
    asm.Set(name=SET_CORNER_A, vertices=vA)
    asm.Set(name=SET_CORNER_B, vertices=vB)
    asm.Set(name=SET_CORNER_C, vertices=vC)


def create_corner_stabilization_bcs(model):
    create_corner_stabilization_sets(model)
    specs = [("BC_CORNER_A", SET_CORNER_A, 0.0, 0.0),
             ("BC_CORNER_B", SET_CORNER_B, 0.0, UNSET),
             ("BC_CORNER_C", SET_CORNER_C, UNSET, 0.0)]
    for bc_name, set_name, u1_val, u2_val in specs:
        model.DisplacementBC(name=bc_name, createStepName='Initial', region=_get_region_from_set(model, set_name),
                             u1=u1_val, u2=u2_val, u3=UNSET,
                             ur1=UNSET, ur2=UNSET, ur3=UNSET,
                             amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
        print("Created corner BC:", bc_name)


def create_case_rps_and_couplings(model):
    asm = _get_asm(model)
    for surf in [SURF_LOAD_LEFT, SURF_LOAD_RIGHT, SURF_LOAD_TOP, SURF_LOAD_BOT]:
        _require(surf in asm.surfaces.keys(), "Surface not found: %s" % surf)

    _create_rp_set_outside(model, RP_SET_LEFT, SET_LOWER_LEFT, "left")
    _create_rp_set_outside(model, RP_SET_RIGHT, SET_LOWER_RIGHT, "right")
    _create_rp_set_outside(model, RP_SET_SHEAR_TOP, SET_LOWER_TOP, "top")
    _create_rp_set_outside(model, RP_SET_SHEAR_BOT, SET_LOWER_BOTTOM, "bottom")

    for name in [COUPLING_LEFT, COUPLING_RIGHT, COUPLING_SHEAR_TOP, COUPLING_SHEAR_BOT]:
        _safe_del_constraint(model, name)

    model.Coupling(name=COUPLING_LEFT, controlPoint=asm.sets[RP_SET_LEFT], surface=asm.surfaces[SURF_LOAD_LEFT],
                   influenceRadius=WHOLE_SURFACE, couplingType=DISTRIBUTING, weightingMethod=UNIFORM,
                   localCsys=None, u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=OFF)
    model.Coupling(name=COUPLING_RIGHT, controlPoint=asm.sets[RP_SET_RIGHT], surface=asm.surfaces[SURF_LOAD_RIGHT],
                   influenceRadius=WHOLE_SURFACE, couplingType=DISTRIBUTING, weightingMethod=UNIFORM,
                   localCsys=None, u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=OFF)
    model.Coupling(name=COUPLING_SHEAR_TOP, controlPoint=asm.sets[RP_SET_SHEAR_TOP], surface=asm.surfaces[SURF_LOAD_TOP],
                   influenceRadius=WHOLE_SURFACE, couplingType=DISTRIBUTING, weightingMethod=UNIFORM,
                   localCsys=None, u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=OFF)
    model.Coupling(name=COUPLING_SHEAR_BOT, controlPoint=asm.sets[RP_SET_SHEAR_BOT], surface=asm.surfaces[SURF_LOAD_BOT],
                   influenceRadius=WHOLE_SURFACE, couplingType=DISTRIBUTING, weightingMethod=UNIFORM,
                   localCsys=None, u1=ON, u2=ON, u3=OFF, ur1=OFF, ur2=OFF, ur3=OFF)
    print("Created combined-load RP couplings.")


def create_combined_static_load(model, left_len, right_len, top_len, bottom_len):
    asm = _get_asm(model)
    rp_left = asm.sets[RP_SET_LEFT]
    rp_right = asm.sets[RP_SET_RIGHT]
    rp_top = asm.sets[RP_SET_SHEAR_TOP]
    rp_bot = asm.sets[RP_SET_SHEAR_BOT]

    f_left = COMP_LINE_LOAD_N_PER_MM * left_len
    f_right = COMP_LINE_LOAD_N_PER_MM * right_len
    f_top = SHEAR_LINE_LOAD_N_PER_MM * top_len
    f_bot = SHEAR_LINE_LOAD_N_PER_MM * bottom_len
    f_vleft = SHEAR_LINE_LOAD_N_PER_MM * left_len
    f_vright = SHEAR_LINE_LOAD_N_PER_MM * right_len

    for nm in OLD_LOAD_NAMES: _safe_del_load(model, nm)

    model.ConcentratedForce(name=LOAD_COMB_LEFT_NAME, createStepName=STEP_NAME, region=rp_left,
                            cf1=+f_left, cf2=0.0, cf3=0.0, distributionType=UNIFORM, field='', localCsys=None)
    model.ConcentratedForce(name=LOAD_COMB_RIGHT_NAME, createStepName=STEP_NAME, region=rp_right,
                            cf1=-f_right, cf2=0.0, cf3=0.0, distributionType=UNIFORM, field='', localCsys=None)
    model.ConcentratedForce(name=LOAD_COMB_SHEAR_LEFT_NAME, createStepName=STEP_NAME, region=rp_left,
                            cf1=0.0, cf2=+f_vleft, cf3=0.0, distributionType=UNIFORM, field='', localCsys=None)
    model.ConcentratedForce(name=LOAD_COMB_SHEAR_RIGHT_NAME, createStepName=STEP_NAME, region=rp_right,
                            cf1=0.0, cf2=-f_vright, cf3=0.0, distributionType=UNIFORM, field='', localCsys=None)
    model.ConcentratedForce(name=LOAD_COMB_TOP_NAME, createStepName=STEP_NAME, region=rp_top,
                            cf1=-f_top, cf2=0.0, cf3=0.0, distributionType=UNIFORM, field='', localCsys=None)
    model.ConcentratedForce(name=LOAD_COMB_BOT_NAME, createStepName=STEP_NAME, region=rp_bot,
                            cf1=+f_bot, cf2=0.0, cf3=0.0, distributionType=UNIFORM, field='', localCsys=None)

    print("Created static combined loads:")
    print("  Compression left/right:", +f_left, -f_right)
    print("  Shear left/right:", +f_vleft, -f_vright)
    print("  Shear top/bottom:", -f_top, +f_bot)


def prepare_base_model():
    model = _get_model(BASE_MODEL)
    asm = _get_asm(model)
    for p in PARTS: _require(p in model.parts.keys(), "Missing part: %s" % p)
    for inst in [INST_SFULL, INST_SHALF_PATCHES, INST_LOWERSKIN]:
        _require(inst in asm.instances.keys(), "Missing instance: %s" % inst)

    t_skin, t_stiff = _get_thicknesses_from_design()
    clear_old_loads_and_bcs(model)
    create_material_and_sections(model, t_skin, t_stiff)
    assign_section_to_all_parts(model)
    create_ties(model)

    left_len = _sum_edge_set_length_mm(model, SET_LOWER_LEFT)
    right_len = _sum_edge_set_length_mm(model, SET_LOWER_RIGHT)
    top_len = _sum_edge_set_length_mm(model, SET_LOWER_TOP)
    bottom_len = _sum_edge_set_length_mm(model, SET_LOWER_BOTTOM)

    print("Measured edge lengths:", left_len, right_len, top_len, bottom_len)
    return left_len, right_len, top_len, bottom_len


def copy_static_model_from_base():
    if MODEL_STATIC_COMBINED in mdb.models.keys():
        del mdb.models[MODEL_STATIC_COMBINED]
    mdb.Model(name=MODEL_STATIC_COMBINED, objectToCopy=mdb.models[BASE_MODEL])
    print("Created model:", MODEL_STATIC_COMBINED)


def configure_static_combined_model(left_len, right_len, top_len, bottom_len):
    model = _get_model(MODEL_STATIC_COMBINED)
    clear_old_loads_and_bcs(model)
    create_static_step(model)
    create_case_rps_and_couplings(model)
    create_simply_supported_u3_bc(model)
    create_corner_stabilization_bcs(model)
    create_combined_static_load(model, left_len, right_len, top_len, bottom_len)
    print("Configured linear static combined validation model.")


def main():
    left_len, right_len, top_len, bottom_len = prepare_base_model()
    copy_static_model_from_base()
    configure_static_combined_model(left_len, right_len, top_len, bottom_len)
    try:
        if BASE_MODEL in mdb.models.keys():
            del mdb.models[BASE_MODEL]
            print("Deleted base model:", BASE_MODEL)
    except:
        pass
    print("\nDONE: 04_static_combined_validation_omega.py")


if __name__ == "__main__":
    main()
