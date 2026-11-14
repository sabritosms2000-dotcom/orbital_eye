"""Download SPHEREx FITS cutouts for all five targets from IRSA SIA."""
import os
import requests
from pathlib import Path
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
from astropy.io import fits
import numpy as np
from validation.target_registry import get_target, TARGETS
from validation.astrometry import predict_position

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Search radius for cone search (arcminutes)
SEARCH_RADIUS = 1.0

def download_fits(url, dest_path, timeout=30):
    """Download a FITS file from IRSA."""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False

def check_target_in_fits(fits_path, target_ra, target_dec, margin_arcsec=30):
    """Verify the target is within the FITS image using WCS."""
    try:
        with fits.open(fits_path) as hdul:
            wcs = fits.WCS(hdul["IMAGE"].header).celestial
            if not wcs.has_celestial:
                return False, "No celestial WCS"
            target_coord = SkyCoord(ra=target_ra*u.deg, dec=target_dec*u.deg, frame='icrs')
            x, y = wcs.world_to_pixel(target_coord)
            h, w = hdul["IMAGE"].data.shape
            inside = (np.isfinite(x) and np.isfinite(y) and 0 <= x < w and 0 <= y < h)
            # Also check margin
            pixel_scale = np.sqrt(wcs.proj_plane_pixel_area().to_value("deg2")) * 3600  # arcsec/pixel
            margin_pix = margin_arcsec / pixel_scale
            margin_inside = (np.isfinite(x) and np.isfinite(y) and -margin_pix <= x < w + margin_pix and -margin_pix <= y < h + margin_pix)
            return inside, f"Pixel: ({x:.1f}, {y:.1f}), Image: {w}x{h}, Inside: {inside}, MarginInside: {margin_inside}"
    except Exception as e:
        return False, f"FITS check failed: {e}"

def get_observations_for_target(target_id, max_per_band=2):
    """Get SIA records for a target, grouped by band, limited per band."""
    target = get_target(target_id)
    ref = target["reference"]
    coord = SkyCoord(ra=ref["ra_deg"]*u.deg, dec=ref["dec_deg"]*u.deg, frame="icrs")
    
    print(f"Querying IRSA for {target['name']}...")
    table = Irsa.query_sia(pos=(coord, SEARCH_RADIUS*u.arcmin), collection="spherex_dr1")
    print(f"  Found {len(table)} records")
    
    # Group by band and date
    by_band = {}
    for row in table:
        band = row.get("energy_bandpassname")
        if not band:
            continue
        if band not in by_band:
            by_band[band] = []
        by_band[band].append(row)
    
    # Sort each band by date and take first N
    selected = []
    for band, rows in by_band.items():
        rows_sorted = sorted(rows, key=lambda r: r.get("t_min", 0))
        for row in rows_sorted[:max_per_band]:
            selected.append(row)
    
    return selected

def main():
    targets = ["barnards_star", "epsilon_indi_b", "wise_0855", "rw_aurigae", "r_draconis"]
    
    for target_id in targets:
        target = get_target(target_id)
        ref = target["reference"]
        ra, dec = ref["ra_deg"], ref["dec_deg"]
        print(f"\n{'='*60}")
        print(f"Target: {target['name']} (RA={ra}, Dec={dec})")
        print(f"{'='*60}")
        
        # Get observations
        observations = get_observations_for_target(target_id, max_per_band=2)
        print(f"Selected {len(observations)} observations to download")
        
        # Download each
        local_fits = []
        for i, row in enumerate(observations):
            obs_id = row.get("obs_id")
            band = row.get("energy_bandpassname")
            url = row.get("access_url")
            mjd = row.get("t_min")
            date_str = Time(float(mjd), format="mjd").isot[:10] if mjd else "unknown"
            
            # Create filename
            fname = f"{target_id}_{obs_id}_{band}.fits"
            dest = DATA_DIR / fname
            
            if dest.exists():
                print(f"  [{i+1}/{len(observations)}] {fname} already exists")
            else:
                print(f"  [{i+1}/{len(observations)}] Downloading {fname} ({band}, {date_str})...")
                if download_fits(url, dest):
                    print(f"    Downloaded: {dest.stat().st_size / 1e6:.1f} MB")
                else:
                    continue
            
            # Verify target is in image
            inside, info = check_target_in_fits(dest, ra, dec)
            print(f"    WCS check: {info}")
            
            if inside:
                local_fits.append({
                    "observation_id": f"{target_id}_{i+1}",
                    "relative_path": f"data/{fname}"
                })
            else:
                print(f"    WARNING: Target not in image, skipping")
        
        print(f"\n  Valid local FITS for {target['name']}: {len(local_fits)}")
        for lf in local_fits:
            print(f"    - {lf['observation_id']}: {lf['relative_path']}")

if __name__ == "__main__":
    main()