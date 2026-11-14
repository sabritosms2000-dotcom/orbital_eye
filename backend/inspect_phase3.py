
from pathlib import Path

import numpy as np
import astropy.units as u

from astropy.io import fits
from astropy.wcs import WCS


# ==========================================
# PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FILES = [
    DATA_DIR / "wise0855_first_cutout.fits",
    DATA_DIR / "wise0855_second_cutout.fits",
]


# ==========================================
# INSPECT FITS FILES
# ==========================================

for file_path in FILES:

    print("\n" + "=" * 60)
    print("FILE:", file_path.name)
    print("=" * 60)

    if not file_path.exists():
        print("ERROR: File not found:", file_path)
        continue

    with fits.open(file_path) as hdul:

        # 1. FITS EXTENSIONS
        print("\nHDU EXTENSIONS:")

        for hdu in hdul:
            print(
                hdu.name,
                "shape:",
                getattr(hdu.data, "shape", None)
            )

        # 2. IMAGE AND HEADER
        image_hdu = hdul["IMAGE"]
        header = image_hdu.header
        image = np.asarray(image_hdu.data, dtype=float)

        print("\nOBSERVATION METADATA:")

        for key in [
            "DATE-OBS",
            "MJD-OBS",
            "BUNIT",
            "BAND",
            "FILTER",
        ]:
            print(key, "=", header.get(key))

        # 3. WCS
        print("\nWCS:")

        wcs = WCS(header).celestial
        print("Valid celestial WCS:", wcs.has_celestial)

        pixel_scales = wcs.proj_plane_pixel_scales()

        pixel_scales_arcsec = [
            scale.to_value(u.arcsec)
            for scale in pixel_scales
        ]

        print(
            "Pixel scale (arcsec/pixel):",
            pixel_scales_arcsec
        )

        # 4. IMAGE STATISTICS
        print("\nIMAGE:")

        print("Shape:", image.shape)
        print("Finite pixels:", int(np.isfinite(image).sum()))
        print("Median:", float(np.nanmedian(image)))
        print("Standard deviation:", float(np.nanstd(image)))

        # 5. VARIANCE
        print("\nVARIANCE:")

        variance = np.asarray(
            hdul["VARIANCE"].data,
            dtype=float
        )

        valid_variance = variance[
            np.isfinite(variance) & (variance >= 0)
        ]

        print("Valid pixels:", valid_variance.size)

        if valid_variance.size:
            median_variance = float(np.median(valid_variance))

            print("Median variance:", median_variance)
            print(
                "Median standard uncertainty:",
                float(np.sqrt(median_variance))
            )

        # 6. FLAGS
        print("\nFLAGS:")

        flags = np.asarray(hdul["FLAGS"].data)
        flag_values, flag_counts = np.unique(
            flags,
            return_counts=True
        )

        for value, count in zip(flag_values, flag_counts):
            print("Flag:", int(value), "Count:", int(count))

        # 7. EPSF TABLE
        print("\nEPSF:")

        epsf_hdu = hdul["EPSF"]

        if epsf_hdu.data is not None:

            print("EPSF columns:", epsf_hdu.columns.names)

            for row_index, row in enumerate(epsf_hdu.data):

                print("\nEPSF row:", row_index)

                for column in epsf_hdu.columns.names:
                    value = row[column]

                    if column == "EPSF":
                        psf = np.asarray(value, dtype=float)

                        print("PSF shape:", psf.shape)
                        print(
                            "PSF finite pixels:",
                            int(np.isfinite(psf).sum())
                        )
                        print(
                            "PSF maximum:",
                            float(np.nanmax(psf))
                        )
                        print(
                            "PSF minimum:",
                            float(np.nanmin(psf))
                        )
                        print(
                            "PSF sum:",
                            float(np.nansum(psf))
                        )
                    else:
                        print(column, "=", value)

        else:
            print("EPSF data unavailable")

        # 8. ZODI
        print("\nZODI:")

        zodi_data = hdul["ZODI"].data

        if zodi_data is not None:
            zodi = np.asarray(zodi_data, dtype=float)

            print("Shape:", zodi.shape)
            print("Median:", float(np.nanmedian(zodi)))
        else:
            print("ZODI data unavailable")


# ==========================================
# FINISHED
# ==========================================

print("\n" + "=" * 60)
print("PHASE 3 DIAGNOSTIC COMPLETE")
print("=" * 60)
