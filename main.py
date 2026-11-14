
from astropy.io import fits

file_path = "level2_2025W19_2B_0073_2D3_spx_l2b-v27-2026-198.fits"

# Open the FITS file
hdul = fits.open(file_path)

# Display the structure
print("FITS File Structure:")
hdul.info()

# Display the number of HDUs
print("\nNumber of HDUs:", len(hdul))

# Display the primary header
print("\nPrimary Header:")
print(hdul[0].header)

# Close the file
hdul.close()
