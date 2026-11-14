
from astropy.io import fits

FILES = [
    "../data/wise0855_first_cutout.fits",
    "../data/wise0855_second_cutout.fits"
]

KEYWORDS = [
    "DATE-OBS",
    "MJD-OBS",
    "MJD-AVG",
    "EXPTIME",
    "RA",
    "DEC",
    "CRVAL1",
    "CRVAL2",
    "CRPIX1",
    "CRPIX2",
    "RADESYS",
    "EQUINOX",
    "OBSGEO-X",
    "OBSGEO-Y",
    "OBSGEO-Z",
    "TELESCOP",
    "OBSERVAT"
]

for path in FILES:
    print("\n" + "=" * 60)
    print(path)
    print("=" * 60)

    with fits.open(path) as hdul:
        header = hdul["IMAGE"].header

        for key in KEYWORDS:
            if key in header:
                print(f"{key}: {header[key]}")

        print("\nOther relevant keywords:")

        for key in header:
            if any(term in key.upper() for term in
                   ["OBSGEO", "OBSERV", "SPACECRAFT", "EPHEM"]):
                print(f"{key}: {header[key]}")
