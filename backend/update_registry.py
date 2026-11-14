"""Update target_registry.py with downloaded local FITS paths."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Scan for valid FITS files (non-zero, has IMAGE/FLAGS/VARIANCE extensions)
def is_valid_fits(path):
    try:
        from astropy.io import fits
        with fits.open(path, memmap=True) as hdul:
            return all(x in hdul for x in ("IMAGE", "FLAGS", "VARIANCE")) and hdul["IMAGE"].data is not None
    except:
        return False

# Collect valid files by target
target_files = {}
for f in DATA_DIR.glob("*.fits"):
    if f.stat().st_size == 0:
        continue
    if not is_valid_fits(f):
        continue
    # Parse target_id from filename: targetid_obsid_band.fits
    name = f.stem
    parts = name.split("_")
    if len(parts) >= 2:
        target_id = parts[0]
        # Normalize target_id to match registry keys
        if target_id == "barnards":
            target_id = "barnards_star"
        elif target_id == "epsilon":
            target_id = "epsilon_indi_b"
        elif target_id == "rw":
            target_id = "rw_aurigae"
        elif target_id in ("wise0855", "wise"):
            target_id = "wise_0855"
        if target_id not in target_files:
            target_files[target_id] = []
        target_files[target_id].append(str(f.relative_to(ROOT)).replace("\\", "/"))

print("Valid FITS files by target:")
for tid, files in target_files.items():
    print(f"  {tid}: {len(files)} files")

# Read current registry
registry_path = ROOT / "backend" / "validation" / "target_registry.py"
content = registry_path.read_text(encoding="utf-8")

# Update local_fits for each target
for target_id, files in target_files.items():
    local_fits_entries = []
    for i, f in enumerate(files):
        obs_id = Path(f).stem.replace(f"{Path(f).stem.split('_')[0]}_", "")
        local_fits_entries.append(f'            {{"observation_id": "{target_id}_{i+1}", "relative_path": "{f}"}}')
    
    local_fits_str = ",\n".join(local_fits_entries)
    
    # Find the target block and replace its local_fits array
    # Pattern: "target_id": { ... "local_fits": [ ... ] }
    pattern = rf'("{re.escape(target_id)}":\s*\{{[^}}]*"local_fits":\s*)\[([^\]]*)\]'
    replacement = rf'\1[\n{local_fits_str}\n        ]'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write updated registry
registry_path.write_text(content, encoding="utf-8")
print("\nRegistry updated!")