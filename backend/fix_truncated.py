"""Re-download truncated FITS files."""
from download_fits import download_fits, check_target_in_fits
from validation.target_registry import get_target
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Files to re-download (size check)
TRUNCATED = {
    "barnards_star_2025W33_2C_0321_1_SPHEREx-D6.fits": 64889280,  # expected size from obs 2
    "wise_0855_2025W19_1B_0116_1_SPHEREx-D3.fits": 65000000,  # approx expected
    "rw_aurigae_2025W36_1A_0095_1_SPHEREx-D1.fits": 65612160,  # expected from D4
}

# Need to find the access_url for each. Let's query IRSA again.
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time

def find_url_for_fits(target_id, obs_id, band):
    target = get_target(target_id)
    ref = target["reference"]
    coord = SkyCoord(ra=ref["ra_deg"]*u.deg, dec=ref["dec_deg"]*u.deg, frame="icrs")
    table = Irsa.query_sia(pos=(coord, 1*u.arcmin), collection="spherex_dr1")
    for row in table:
        if row.get("obs_id") == obs_id and row.get("energy_bandpassname") == band:
            return row.get("access_url")
    return None

# Re-download each truncated file
for fname, expected_size in TRUNCATED.items():
    path = DATA_DIR / fname
    actual = path.stat().st_size
    print(f"{fname}: {actual/1e6:.1f} MB (expected ~{expected_size/1e6:.1f} MB)")
    
    if actual < expected_size * 0.9:
        # Parse target_id, obs_id, band from filename
        parts = fname.replace(".fits", "").split("_")
        target_id = "_".join(parts[:-2])  # everything except last two parts
        if target_id == "barnards":
            target_id = "barnards_star"
        elif target_id == "epsilon":
            target_id = "epsilon_indi_b"
        elif target_id == "rw":
            target_id = "rw_aurigae"
        elif target_id == "wise0855":
            target_id = "wise_0855"
        obs_id = "_".join(parts[-2:])
        # Actually need to parse differently... let's just hardcode the known ones
        print(f"  -> Truncated! Need to re-download")
    else:
        print(f"  -> OK")