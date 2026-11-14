"""Download FITS for remaining 3 targets."""
from download_fits import get_observations_for_target, download_fits, check_target_in_fits
from validation.target_registry import get_target
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time

for target_id in ['epsilon_indi_b', 'rw_aurigae', 'r_draconis']:
    target = get_target(target_id)
    ref = target["reference"]
    ra, dec = ref["ra_deg"], ref["dec_deg"]
    print(f"Target: {target['name']}")
    obs = get_observations_for_target(target_id, max_per_band=1)
    print(f"  Selected {len(obs)} observations")
    for i, row in enumerate(obs):
        obs_id = row.get("obs_id")
        band = row.get("energy_bandpassname")
        url = row.get("access_url")
        mjd = row.get("t_min")
        date_str = Time(float(mjd), format="mjd").isot[:10] if mjd else "unknown"
        fname = f"{target_id}_{obs_id}_{band}.fits"
        dest = f"C:\\Users\\standalone\\Desktop\\orbital_eye\\andrew\\The project\\The project\\SPHEREx_Project\\data\\{fname}"
        print(f"  Downloading {fname} ({band}, {date_str})...")
        if download_fits(url, dest):
            print(f"    OK")
            inside, info = check_target_in_fits(dest, ra, dec)
            print(f"    WCS: {info}")
        else:
            print(f"    FAILED")