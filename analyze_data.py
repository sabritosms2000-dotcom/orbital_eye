
from astropy.io import fits
import numpy as np

file_path = "level2_2025W19_2B_0073_2D3_spx_l2b-v27-2026-198.fits"

with fits.open(file_path) as hdul:

    print("===== SPHEREx Data Analysis =====")

    # Examine each HDU
    for hdu in hdul:

        print("\n------------------------")
        print("HDU:", hdu.name)
        print("Type:", type(hdu).__name__)

        if hdu.data is not None:

            print("Shape:", hdu.data.shape)
            print("Data type:", hdu.data.dtype)

            if isinstance(hdu.data, np.ndarray) and hdu.data.dtype.names is None:
                data = hdu.data.astype(float)

                print("Minimum:", np.nanmin(data))
                print("Maximum:", np.nanmax(data))
                print("Mean:", np.nanmean(data))

            elif hdu.data.dtype.names:
                print("Table columns:", hdu.data.dtype.names)

        # Display important header information
        print("BUNIT:", hdu.header.get("BUNIT", "Not specified"))
        print("EXTNAME:", hdu.header.get("EXTNAME", "Primary"))

    print("\n===== Analysis Complete =====")
