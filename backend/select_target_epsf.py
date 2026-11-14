
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np


FILES = [
    {
        "path": "../data/wise0855_first_cutout.fits",
        "x": 28.223681427148,
        "y": 28.737146168733375
    },
    {
        "path": "../data/wise0855_second_cutout.fits",
        "x": 28.91226193455047,
        "y": 29.00827931613042
    }
]


def remove_sip_keywords(header):
    clean_header = header.copy()

    for key in list(clean_header.keys()):
        if (
            key in ("A_ORDER", "B_ORDER", "AP_ORDER", "BP_ORDER")
            or key.startswith(("A_", "B_", "AP_", "BP_"))
        ):
            del clean_header[key]

    return clean_header


for item in FILES:

    print("\n" + "=" * 55)
    print(item["path"])
    print("=" * 55)

    with fits.open(item["path"]) as hdul:

        header = hdul["IMAGE"].header
        epsf = hdul["EPSF"].data

        # Clean header to avoid SIP warnings
        clean_header = remove_sip_keywords(header)

        # Get wavelength and bandwidth at target pixel
        wave_wcs = WCS(clean_header, fobj=hdul, key="W")

        wavelength, bandwidth = wave_wcs.all_pix2world(
            [[item["x"], item["y"]]], 0
        )[0]

        print(f"Target wavelength: {wavelength:.6f} um")
        print(f"Target bandwidth: {bandwidth:.6f} um")

        # Convert target position to active detector coordinates
        active_wcs = WCS(clean_header, key="A")

        active_x, active_y = active_wcs.all_pix2world(
            [[item["x"], item["y"]]], 0
        )[0]

        print("\nTarget detector position:")
        print("X:", round(active_x, 3))
        print("Y:", round(active_y, 3))

        # Find nearest spatial EPSF model
        distances = np.sqrt(
            (epsf["XCENTER"] - active_x) ** 2
            + (epsf["YCENTER"] - active_y) ** 2
        )

        index = np.argmin(distances)
        row = epsf[index]

        print("\nNearest spatial EPSF:")
        print("Row:", index)
        print("BINX:", row["BINX"])
        print("BINY:", row["BINY"])
        print("Distance:", round(distances[index], 3))

        print(f"EPSF CWAVE: {row['CWAVE']:.6f} um")
        print(f"EPSF CBAND: {row['CBAND']:.6f} um")

        print(
            "Wavelength difference:",
            round(abs(wavelength - row["CWAVE"]), 6),
            "um"
        )

        # Check whether target is inside selected EPSF zone
        print("\nEPSF zone information:")

        print("X center:", row["XCENTER"])
        print("Y center:", row["YCENTER"])
        print("X width:", row["XWIDTH"])
        print("Y width:", row["YWIDTH"])

        inside_x = (
            abs(active_x - row["XCENTER"]) <= row["XWIDTH"] / 2
        )

        inside_y = (
            abs(active_y - row["YCENTER"]) <= row["YWIDTH"] / 2
        )

        print("\nIs target inside selected EPSF zone?")
        print("Inside X:", inside_x)
        print("Inside Y:", inside_y)
        print("Inside zone:", inside_x and inside_y)

        print("\n" + "-" * 55)
