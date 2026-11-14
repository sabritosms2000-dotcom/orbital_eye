"""Update target_registry.py with R Draconis local FITS."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
registry_path = ROOT / "backend" / "validation" / "target_registry.py"
content = registry_path.read_text(encoding="utf-8")

# Find r_draconis target and replace its local_fits
import re

# The new local_fits block for r_draconis
new_fits = '''        "local_fits": [
            {"observation_id": "r_draconis_1", "relative_path": "data/r_draconis_2025W20_2D_0243_1_SPHEREx-D3.fits"},
            {"observation_id": "r_draconis_2", "relative_path": "data/r_draconis_2025W20_2D_0243_2_SPHEREx-D6.fits"},
        ]'''

# Pattern: find "r_draconis": { ... "local_fits": [] }
pattern = r'("r_draconis":\s*\{[^}]*"local_fits":\s*)\[([^\]]*)\]'
replacement = r'\1' + new_fits.split(':', 1)[1].strip()

# Use a more precise approach - replace the entire target block
# Find the start of r_draconis and its local_fits
lines = content.split('\n')
in_r_draconis = False
local_fits_start = -1
local_fits_end = -1
brace_count = 0

for i, line in enumerate(lines):
    if '"r_draconis"' in line and ':' in line:
        in_r_draconis = True
    if in_r_draconis:
        if '"local_fits"' in line:
            local_fits_start = i
        if local_fits_start >= 0:
            if '[' in line:
                brace_count += line.count('[')
            if ']' in line:
                brace_count -= line.count(']')
                if brace_count <= 0:
                    local_fits_end = i
                    break

if local_fits_start >= 0 and local_fits_end >= 0:
    # Replace lines[local_fits_start:local_fits_end+1]
    indent = ' ' * 8
    new_lines = [f'{indent}"local_fits": [']
    new_lines.append(f'{indent}    {{"observation_id": "r_draconis_1", "relative_path": "data/r_draconis_2025W20_2D_0243_1_SPHEREx-D3.fits"}},')
    new_lines.append(f'{indent}    {{"observation_id": "r_draconis_2", "relative_path": "data/r_draconis_2025W20_2D_0243_2_SPHEREx-D6.fits"}},')
    new_lines.append(f'{indent}]')
    lines = lines[:local_fits_start] + new_lines + lines[local_fits_end+1:]
    content = '\n'.join(lines)
    registry_path.write_text(content, encoding="utf-8")
    print("R Draconis local_fits updated!")
else:
    print("Could not find local_fits for r_draconis")