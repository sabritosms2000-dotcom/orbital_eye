
from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt

file_path = "level2_2025W19_2B_0073_2D3_spx_l2b-v27-2026-198.fits"

with fits.open(file_path) as hdul:

    wave_table = hdul["WCS-WAVE"].data[0]

    x = wave_table["X"]
    y = wave_table["Y"]
    values = wave_table["VALUES"]

    # Extract wavelength and bandwidth
    wavelength = values[:, :, 0]
    bandwidth = values[:, :, 1]

    X, Y = np.meshgrid(x, y)

    # Plot wavelength control-point map
    plt.figure(figsize=(10, 7))

    plot = plt.pcolormesh(
        X, Y, wavelength,
        shading="auto",
        cmap="viridis"
    )

    plt.colorbar(plot, label="Wavelength (check table units)")
    plt.xlabel("Detector X Position")
    plt.ylabel("Detector Y Position")
    plt.title("SPHEREx Wavelength Control-Point Map")

    plt.show()

    # Plot bandwidth control-point map
    plt.figure(figsize=(10, 7))

    plot = plt.pcolormesh(
        X, Y, bandwidth,
        shading="auto",
        cmap="plasma"
    )

    plt.colorbar(plot, label="Bandwidth (check table units)")
    plt.xlabel("Detector X Position")
    plt.ylabel("Detector Y Position")
    plt.title("SPHEREx Bandwidth Control-Point Map")

    plt.show()
