"""Update target_registry.py with downloaded local FITS paths - direct edit."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Manually define the local_fits for each target based on downloaded files
LOCAL_FITS = {
    "barnards_star": [
        {"observation_id": "barnards_star_1", "relative_path": "data/barnards_star_2025W33_2C_0321_1_SPHEREx-D3.fits"},
        {"observation_id": "barnards_star_2", "relative_path": "data/barnards_star_2025W33_2C_0321_1_SPHEREx-D6.fits"},
        {"observation_id": "barnards_star_3", "relative_path": "data/barnards_star_2025W33_2C_0321_2_SPHEREx-D3.fits"},
        {"observation_id": "barnards_star_4", "relative_path": "data/barnards_star_2025W33_2C_0321_2_SPHEREx-D6.fits"},
        {"observation_id": "barnards_star_5", "relative_path": "data/barnards_star_2025W34_2B_0090_4_SPHEREx-D2.fits"},
        {"observation_id": "barnards_star_6", "relative_path": "data/barnards_star_2025W34_2B_0090_4_SPHEREx-D5.fits"},
        {"observation_id": "barnards_star_7", "relative_path": "data/barnards_star_2025W34_2B_0557_1_SPHEREx-D2.fits"},
        {"observation_id": "barnards_star_8", "relative_path": "data/barnards_star_2025W34_2B_0557_1_SPHEREx-D5.fits"},
        {"observation_id": "barnards_star_9", "relative_path": "data/barnards_star_2025W35_1A_0432_4_SPHEREx-D1.fits"},
        {"observation_id": "barnards_star_10", "relative_path": "data/barnards_star_2025W35_1A_0432_4_SPHEREx-D4.fits"},
        {"observation_id": "barnards_star_11", "relative_path": "data/barnards_star_2025W35_1A_0658_1_SPHEREx-D1.fits"},
        {"observation_id": "barnards_star_12", "relative_path": "data/barnards_star_2025W35_1A_0658_1_SPHEREx-D4.fits"},
    ],
    "epsilon_indi_b": [
        {"observation_id": "epsilon_indi_b_1", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_1_SPHEREx-D2.fits"},
        {"observation_id": "epsilon_indi_b_2", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_1_SPHEREx-D5.fits"},
        {"observation_id": "epsilon_indi_b_3", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_2_SPHEREx-D2.fits"},
        {"observation_id": "epsilon_indi_b_4", "relative_path": "data/epsilon_indi_b_2025W17_4B_0017_2_SPHEREx-D5.fits"},
        {"observation_id": "epsilon_indi_b_5", "relative_path": "data/epsilon_indi_b_2025W17_4B_0077_2_SPHEREx-D4.fits"},
        {"observation_id": "epsilon_indi_b_6", "relative_path": "data/epsilon_indi_b_2025W17_4B_0077_3_SPHEREx-D1.fits"},
        {"observation_id": "epsilon_indi_b_7", "relative_path": "data/epsilon_indi_b_2025W17_4B_0077_3_SPHEREx-D4.fits"},
        {"observation_id": "epsilon_indi_b_8", "relative_path": "data/epsilon_indi_b_2025W17_4B_0468_1_SPHEREx-D1.fits"},
        {"observation_id": "epsilon_indi_b_9", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_2_SPHEREx-D3.fits"},
        {"observation_id": "epsilon_indi_b_10", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_2_SPHEREx-D6.fits"},
        {"observation_id": "epsilon_indi_b_11", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_3_SPHEREx-D3.fits"},
        {"observation_id": "epsilon_indi_b_12", "relative_path": "data/epsilon_indi_b_2025W18_1B_0081_3_SPHEREx-D6.fits"},
    ],
    "wise_0855": [
        {"observation_id": "first", "relative_path": "data/wise0855_first_cutout.fits"},
        {"observation_id": "second", "relative_path": "data/wise0855_second_cutout.fits"},
        {"observation_id": "wise_0855_3", "relative_path": "data/wise_0855_2025W19_1B_0116_1_SPHEREx-D3.fits"},
    ],
    "rw_aurigae": [
        {"observation_id": "rw_aurigae_1", "relative_path": "data/rw_aurigae_2025W36_1A_0095_1_SPHEREx-D1.fits"},
        {"observation_id": "rw_aurigae_2", "relative_path": "data/rw_aurigae_2025W36_1A_0095_1_SPHEREx-D4.fits"},
    ],
}

# Read the file
registry_path = ROOT / "backend" / "validation" / "target_registry.py"
lines = registry_path.read_text(encoding="utf-8").splitlines()

# Find and replace local_fits for each target
import re
output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    output_lines.append(line)
    
    # Check if this line contains a target key followed by local_fits on subsequent lines
    for target_id, fits_list in LOCAL_FITS.items():
        if f'"{target_id}":' in line and "local_fits" not in line:
            # Found target start, look for local_fits
            j = i + 1
            while j < len(lines) and '"local_fits"' not in lines[j]:
                j += 1
            if j < len(lines):
                # Found local_fits line, replace from there to closing ]
                k = j
                bracket_count = 0
                while k < len(lines):
                    if "[" in lines[k]:
                        bracket_count += lines[k].count("[")
                    if "]" in lines[k]:
                        bracket_count -= lines[k].count("]")
                        if bracket_count <= 0:
                            break
                    k += 1
                # Replace lines j through k
                indent = " " * 12
                new_fits_lines = [f'{indent}{{']
                new_fits_lines.append(f'{indent}    "local_fits": [')
                for f in fits_list:
                    new_fits_lines.append(f'{indent}        {{"observation_id": "{f["observation_id"]}", "relative_path": "{f["relative_path"]}"}},')
                new_fits_lines.append(f'{indent}    ]')
                new_fits_lines.append(f'{indent}}}')
                # Replace
                output_lines = output_lines[:i+1] + new_fits_lines
                i = k
                break
    i += 1

# Write back
registry_path.write_text("\n".join(output_lines), encoding="utf-8")
print("Registry updated!")