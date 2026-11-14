
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

filename = "wise0855_first_cutout.fits"

with fits.open(filename) as hdul:

    print("===== 1. IMAGE ANALYSIS =====")

    image = hdul["IMAGE"].data
    valid = np.isfinite(image)

    print("Image shape:", image.shape)
    print("Valid pixels:", np.sum(valid))
    print("Invalid pixels:", np.sum(~valid))

    if np.any(valid):
        print("Minimum:", np.nanmin(image))
        print("Maximum:", np.nanmax(image))
        print("Mean:", np.nanmean(image))
        print("Median:", np.nanmedian(image))

    print("\n===== 2. VARIANCE ANALYSIS =====")

    variance = hdul["VARIANCE"].data
    valid_var = np.isfinite(variance)

    print("Variance shape:", variance.shape)
    print("Minimum:", np.nanmin(variance))
    print("Maximum:", np.nanmax(variance))
    print("Mean:", np.nanmean(variance))
    print("Negative variance pixels:",
          np.sum(variance < 0))
    print("Invalid variance pixels:",
          np.sum(~valid_var))

    print("\n===== 3. QUALITY FLAGS =====")

    flags = hdul["FLAGS"].data

    print("Flags shape:", flags.shape)
    print("Minimum flag:", np.min(flags))
    print("Maximum flag:", np.max(flags))
    print("Unique flag values:", len(np.unique(flags)))

    values, counts = np.unique(flags, return_counts=True)
    order = np.argsort(counts)[::-1]

    print("\nMost common flag values:")
    for i in order[:10]:
        print("Flag:", values[i], "| Pixels:", counts[i])

    print("\n===== 4. IMAGE HEADER / WCS =====")

    header = hdul["IMAGE"].header

    for key in [
        "BUNIT", "TELESCOP", "INSTRUME",
        "DATE-OBS", "MJD-OBS",
        "CRVAL1", "CRVAL2",
        "CRPIX1", "CRPIX2",
        "CTYPE1", "CTYPE2",
        "CDELT1", "CDELT2"
    ]:
        if key in header:
            print(key, "=", header[key])

    try:
        wcs = WCS(header)
        center_x = (image.shape[1] - 1) / 2
        center_y = (image.shape[0] - 1) / 2

        sky = wcs.pixel_to_world(center_x, center_y)

        print("\nCutout center sky coordinates:")
        print(sky)

    except Exception as e:
        print("Could not calculate WCS coordinates:", e)

    print("\n===== 5. EPSF INFORMATION =====")

    epsf = hdul["EPSF"].data

    print("EPSF records:", len(epsf))
    print("EPSF columns:", hdul["EPSF"].columns.names)

    print("\n===== 6. WCS-WAVE INFORMATION =====")

    wave = hdul["WCS-WAVE"].data

    print("WCS-WAVE columns:",
          hdul["WCS-WAVE"].columns.names)

    for name in hdul["WCS-WAVE"].columns.names:
        print(name, "shape:", np.shape(wave[name][0]))

print("\n===== CUTOUT ANALYSIS COMPLETE =====")
