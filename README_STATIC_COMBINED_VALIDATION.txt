STATIC COMBINED VALIDATION SCRIPTS - OMEGA GA

Purpose
-------
After the Omega GA finishes, run a separate linear static validation on the best 2-3 selected designs.
This validation uses the COMBINED load case, not compression-only.

Main command
------------
1) Copy all scripts in this folder into:
   C:\Rhino Hiwi\Thesis\cad_to_stp\Trial_I and_C_seperate\Omega_Profiles_voronoi\Omega_GA_sripts\

2) After GA has completed, run:
   python RUN_STATIC_VALIDATION_SELECTED_omega.py --top 3

Optional:
   python RUN_STATIC_VALIDATION_SELECTED_omega.py --csv "C:\path\to\ga_master_log_....csv" --top 2

What the runner does
--------------------
- Finds the latest GA CSV if --csv is not provided.
- Selects the top successful designs by lowest fitness_paper.
- Runs Abaqus/CAE noGUI for each selected case.
- Stores static validation outputs in each case folder:
      <case_dir>\Results_Static_Combined\

Important outputs
-----------------
For each selected case:
  <case_dir>\Results_Static_Combined\Static_Combined.odb
  <case_dir>\Results_Static_Combined\Static_Combined.inp
  <case_dir>\Results_Static_Combined\static_combined_summary.json
  <case_dir>\Results_Static_Combined\static_combined_summary.csv

Aggregate outputs:
  GA_omega_results\GAomega_result_for_m0.6_L0.4_coords10\selected_static_cases.json
  GA_omega_results\GAomega_result_for_m0.6_L0.4_coords10\static_validation_selected_summary.json
  GA_omega_results\GAomega_result_for_m0.6_L0.4_coords10\static_validation_selected_summary.csv

Values extracted
----------------
- max_U_mag
- max_abs_U1, max_abs_U2, max_abs_U3
- S11_min/max
- S22_min/max
- S33_min/max
- max_abs_S33
- max_mises

Images
------
No images are generated automatically. Open Static_Combined.odb manually in Abaqus/CAE
for U/U3, S11, S22, S33, and Mises contour images.

Notes
-----
This validation is separate from the GA/buckling pipeline. It does not change the original Results folder.
