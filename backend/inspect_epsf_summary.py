
from astropy.io import fits
import numpy as np

FILES = [
    "../data/wise0855_first_cutout.fits",
    "../data/wise0855_second_cutout.fits"
]

for file_path in FILES:
    print("\n" + "=" * 60)
    print("FILE:", file_path)
    print("=" * 60)

    with fits.open(file_path) as hdul:
        # EPSF table
        epsf = hdul["EPSF"].data

        print("\nEPSF TABLE")
        print("Number of rows:", len(epsf))
        print("Columns:", epsf.columns.names)

        for name in ["BINX", "BINY", "XCENTER", "YCENTER",
                     "CWAVE", "CBAND", "NSTAR"]:
            if name in epsf.columns.names:
                values = np.asarray(epsf[name], dtype=float)
                print(
                    f"{name}: min={np.nanmin(values):.4f}, "
                    f"max={np.nanmax(values):.4f}"
                )

        print("\nFIRST 5 EPSF ROWS")
        for i in range(min(5, len(epsf))):
            row = epsf[i]
            print(
                i,
                "BINX:", row["BINX"],
                "BINY:", row["BINY"],
                "XCENTER:", row["XCENTER"],
                "YCENTER:", row["YCENTER"],
                "CWAVE:", row["CWAVE"],
                "CBAND:", row["CBAND"]
            )

        # WCS-WAVE extension
        print("\nWCS-WAVE EXTENSION")
        wave = hdul["WCS-WAVE"]
        print("Header:")
        print(repr(wave.header))

        if wave.data is not None:
            print("Data type:", wave.data.dtype)
            print("Data shape:", wave.data.shape)
            print("Data:")
            print(wave.data)
