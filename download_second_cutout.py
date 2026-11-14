
import requests
from astropy.io import fits

url = "https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2026W20_1A/l2b-v27-2026-246/3/level2_2026W20_1A_0033_1D3_spx_l2b-v27-2026-246.fits?center=133.79513,-7.24515d&size=0.1"

filename = "wise0855_second_cutout.fits"

print("Downloading second WISE 0855 cutout...")

response = requests.get(url, timeout=120)
response.raise_for_status()

with open(filename, "wb") as f:
    f.write(response.content)

print("Download complete!")
print("File size:", len(response.content), "bytes")

# Verify FITS file
with fits.open(filename) as hdul:
    print("\n===== SECOND FITS HDU INFORMATION =====")
    hdul.info()

    print("\n===== IMAGE SHAPES =====")
    for i, hdu in enumerate(hdul):
        if hdu.data is not None:
            print(i, hdu.name, hdu.data.shape)

print("\nSaved:", filename)
