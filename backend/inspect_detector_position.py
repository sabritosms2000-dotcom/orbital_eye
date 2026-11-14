
from astropy.io import fits

FILES = [
    "../data/wise0855_first_cutout.fits",
    "../data/wise0855_second_cutout.fits"
]

for file_path in FILES:
    print("\n" + "=" * 60)
    print(file_path)
    print("=" * 60)

    with fits.open(file_path) as hdul:
        for hdu in hdul:
            print("\nHDU:", hdu.name)
            print("Shape:", getattr(hdu.data, "shape", None))

            if hdu.name == "IMAGE":
                print("\nALL IMAGE HEADER KEYWORDS:")
                for key, value in hdu.header.items():
                    print(f"{key} = {value}")

            if hdu.name == "EPSF":
                print("\nEPSF TABLE HEADER:")
                for key, value in hdu.header.items():
                    print(f"{key} = {value}")
