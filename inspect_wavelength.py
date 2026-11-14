
from astropy.io import fits
import numpy as np

file_path = "level2_2025W19_2B_0073_2D3_spx_l2b-v27-2026-198.fits"

with fits.open(file_path) as hdul:

    wave_table = hdul["WCS-WAVE"].data[0]

    x_points = wave_table["X"]
    y_points = wave_table["Y"]
    values = wave_table["VALUES"]

    print("===== WAVELENGTH INFORMATION =====")

    print("X control points:", x_points)
    print("Y control points:", y_points)

    print("\nValues shape:", values.shape)

    print("\nSample wavelength values:")

    for i in range(min(3, len(y_points))):
        for j in range(min(3, len(x_points))):

            wavelength = values[i, j, 0]
            bandwidth = values[i, j, 1]

            print(
                f"X={x_points[j]}, Y={y_points[i]} | "
                f"Wavelength={wavelength:.6f} | "
                f"Bandwidth={bandwidth:.6f}"
            )

    print("\n===== COMPLETE =====")
