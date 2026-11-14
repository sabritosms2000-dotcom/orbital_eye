
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import skycoord_to_pixel
import numpy as np

# FITS file
filename = "wise0855_first_cutout.fits"

# WISE 0855 coordinates
target = SkyCoord(
    ra=133.79513,
    dec=-7.24515,
    unit="deg",
    frame="icrs"
)

# Flag definitions from FITS header
definitions = {
    1: "TRANSIENT",
    2: "OVERFLOW",
    4: "SUR_ERROR",
    64: "NONFUNC",
    128: "DICHROIC",
    512: "MISSING_DATA",
    1024: "HOT",
    2048: "COLD",
    4096: "FULLSAMPLE",
    16384: "PHANMISS",
    32768: "NONLINEAR",
    131072: "PERSIST",
    524288: "OUTLIER",
    1048576: "CROSSTALK",
    2097152: "SOURCE",
    4194304: "GHOST",
    8388608: "GHOST_FPA",
    16777216: "GHOST_EXT",
    33554432: "STREAK",
    67108864: "BLOOM",
    134217728: "SNOWBALL",
    268435456: "HALO"
}

with fits.open(filename) as hdul:

    image = hdul["IMAGE"].data
    flags = hdul["FLAGS"].data

    # Read WCS from image header
    wcs = WCS(hdul["IMAGE"].header)

    # Convert sky coordinates to pixel coordinates
    x, y = skycoord_to_pixel(target, wcs)

    # Convert NumPy values to regular integers
    x = int(np.asarray(x).item())
    y = int(np.asarray(y).item())

    print("===== WISE 0855 PIXEL LOCATION =====")
    print("X:", x)
    print("Y:", y)

    # Check image boundaries
    if not (0 <= x < image.shape[1] and
            0 <= y < image.shape[0]):

        print("\nTarget is outside the FITS image.")
    
    else:

        print("\n===== TARGET PIXEL VALUES =====")
        print("Image value:", image[y, x])
        print("Flag value:", flags[y, x])

        value = int(flags[y, x])

        print("\n===== TARGET FLAG INTERPRETATION =====")

        found = False

        for bit, name in definitions.items():
            if value & bit:
                print(name)
                found = True

        if not found:
            print("No defined flags set at target pixel.")

    # Count flags across the entire cutout
    print("\n===== FLAG COUNTS IN CUTOUT =====")

    for bit, name in definitions.items():
        count = np.count_nonzero(flags & bit)

        if count > 0:
            print(name, ":", count)

    print("\n===== IMAGE INFORMATION =====")
    print("Image shape:", image.shape)
    print("Flags shape:", flags.shape)

print("\n===== CHECK COMPLETE =====")
