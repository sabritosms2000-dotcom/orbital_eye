
from pathlib import Path

import numpy as np
import astropy.units as u

from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from astropy.coordinates import (
    SkyCoord,
    CartesianRepresentation,
    ICRS,
    get_body_barycentric,
)

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

FILES = {
    "First observation": BASE_DIR / "data" / "wise0855_first_cutout.fits",
    "Second observation": BASE_DIR / "data" / "wise0855_second_cutout.fits",
}

# --------------------------------------------------
# WISE 0855 REFERENCE ASTROMETRY
# --------------------------------------------------

REFERENCE_RA = 133.79513
REFERENCE_DEC = -7.24515

REFERENCE_EPOCH = Time(55320.4, format="mjd", scale="utc")

# Proper motion from Luhman & Esplin (2016)
PM_RA_COSDEC = -8.118 * u.arcsec / u.yr
PM_DEC = 0.680 * u.arcsec / u.yr

# Parallax
PARALLAX = 0.449 * u.arcsec

# Approximate distance from parallax
DISTANCE = (1 / PARALLAX.to(u.arcsec).value) * u.pc

# Radial velocity is not included in this preliminary model
RADIAL_VELOCITY = 0 * u.km / u.s


# --------------------------------------------------
# PROPAGATE TARGET POSITION
# --------------------------------------------------

def predict_target_position(observation_time):

    reference_position = SkyCoord(
        ra=REFERENCE_RA * u.deg,
        dec=REFERENCE_DEC * u.deg,
        distance=DISTANCE,
        pm_ra_cosdec=PM_RA_COSDEC,
        pm_dec=PM_DEC,
        radial_velocity=RADIAL_VELOCITY,
        obstime=REFERENCE_EPOCH,
        frame="icrs",
    )

    # Propagate proper motion to observation date
    barycentric_position = reference_position.apply_space_motion(
        new_obstime=observation_time
    )

    # Approximate annual parallax correction:
    # subtract Earth's barycentric position from the target position
    earth_position = get_body_barycentric(
        "earth",
        observation_time
    )

    target_xyz = barycentric_position.cartesian.xyz.to(u.au)

    observed_xyz = target_xyz - earth_position.xyz.to(u.au)

    observed_position = SkyCoord(
        CartesianRepresentation(observed_xyz),
        frame=ICRS(),
    )

    return observed_position


# --------------------------------------------------
# ANALYZE EACH FITS OBSERVATION
# --------------------------------------------------

def analyze_observation(label, file_path):

    print("\n" + "=" * 65)
    print(label)
    print("=" * 65)

    if not file_path.exists():
        print("ERROR: FITS file not found:", file_path)
        return

    with fits.open(file_path) as hdul:

        image_hdu = hdul["IMAGE"]
        header = image_hdu.header

        observation_time = Time(
            header["MJD-AVG"],
            format="mjd",
            scale="utc",
        )

        wcs = WCS(header).celestial

        # Predict WISE 0855 position at this observation date
        predicted_position = predict_target_position(
            observation_time
        )

        # Convert predicted sky coordinates to image pixels
        x, y = wcs.world_to_pixel(predicted_position)

        height, width = image_hdu.data.shape

        inside = (
            np.isfinite(x)
            and np.isfinite(y)
            and 0 <= x < width
            and 0 <= y < height
        )

        print("Observation date:", observation_time.isot)

        print(
            "Predicted RA:",
            f"{predicted_position.ra.deg:.8f} degrees"
        )

        print(
            "Predicted DEC:",
            f"{predicted_position.dec.deg:.8f} degrees"
        )

        print(f"Predicted pixel X: {x:.3f}")
        print(f"Predicted pixel Y: {y:.3f}")

        print("Inside image:", inside)

        if inside:
            print("WISE 0855 is inside this image.")
        else:
            print("WISE 0855 is outside this image.")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    print("WISE 0855 MOTION DETECTION")
    print("Proper motion + approximate annual parallax")

    for label, file_path in FILES.items():
        analyze_observation(label, file_path)

    print("\nMotion prediction test completed.")

def get_motion_results():
    """Return motion predictions as JSON-serializable data."""
    results = []

    for label, file_path in FILES.items():

        if not file_path.exists():
            results.append({
                "observation": label,
                "status": "error",
                "message": f"FITS file not found: {file_path.name}",
            })
            continue

        with fits.open(file_path) as hdul:
            image_hdu = hdul["IMAGE"]
            header = image_hdu.header

            observation_time = Time(
                header["MJD-AVG"],
                format="mjd",
                scale="utc",
            )

            wcs = WCS(header).celestial

            predicted_position = predict_target_position(
                observation_time
            )

            x, y = wcs.world_to_pixel(predicted_position)

            height, width = image_hdu.data.shape

            inside = (
                np.isfinite(x)
                and np.isfinite(y)
                and 0 <= x < width
                and 0 <= y < height
            )

            results.append({
                "observation": label,
                "status": "success",
                "date": observation_time.isot,
                "predicted_ra": float(predicted_position.ra.deg),
                "predicted_dec": float(predicted_position.dec.deg),
                "pixel_x": float(x),
                "pixel_y": float(y),
                "inside_image": bool(inside),
                "image_width": int(width),
                "image_height": int(height),
            })

    return {
        "target": "WISE 0855",
        "method": "Proper motion + approximate annual parallax",
        "reference_epoch_mjd": 55320.4,
        "observations": results,
        "scientific_note": (
            "Preliminary predicted positions. This is not a confirmed "
            "source detection. The parallax correction is approximate."
        ),
    }
