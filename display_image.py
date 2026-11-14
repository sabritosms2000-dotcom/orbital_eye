
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

file_path = "level2_2025W19_2B_0073_2D3_spx_l2b-v27-2026-198.fits"

# Open FITS file
with fits.open(file_path) as hdul:

    # Extract the main image
    image = hdul["IMAGE"].data

    # Print image information
    print("Image shape:", image.shape)
    print("Minimum value:", np.nanmin(image))
    print("Maximum value:", np.nanmax(image))
    print("Mean value:", np.nanmean(image))

    # Calculate display limits
    vmin, vmax = np.nanpercentile(image, [1, 99])

    # Display the image
    plt.figure(figsize=(10, 8))
    plt.imshow(
        image,
        cmap="gray",
        origin="lower",
        vmin=vmin,
        vmax=vmax
    )

    plt.colorbar(label="Pixel Value")
    plt.title("SPHEREx Scientific Image")
    plt.xlabel("X Pixel")
    plt.ylabel("Y Pixel")
    plt.show()
