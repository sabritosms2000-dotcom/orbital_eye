
from astropy.io import fits

filename = "wise0855_first_cutout.fits"

with fits.open(filename) as hdul:

    print("===== FLAGS HEADER DEFINITIONS =====")

    header = hdul["FLAGS"].header

    for key in header:
        if key.startswith(("MP_", "MSK")):
            print(key, "=", header[key])

    print("\n===== IMAGE HEADER QUALITY COUNTS =====")

    image_header = hdul["IMAGE"].header

    for key in image_header:
        if key.startswith("L2 N_"):
            print(key, "=", image_header[key])

    print("\n===== COMPLETE FLAGS HEADER =====")
    print(repr(header))

print("\n===== DONE =====")
