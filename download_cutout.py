
import requests
from astropy.io import fits

url = "https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W19_1B/l2b-v27-2026-197/3/level2_2025W19_1B_0116_1D3_spx_l2b-v27-2026-197.fits?center=133.79513,-7.24515d&size=0.1"

filename = "wise0855_first_cutout.fits"

print("Downloading WISE 0855 cutout...")

response = requests.get(url, timeout=120)
response.raise_for_status()

with open(filename, "wb") as f:
    f.write(response.content)

print("Download complete!")
print("File size:", len(response.content), "bytes")

# Check that the downloaded file is a valid FITS
with fits.open(filename) as hdul:
    print("\n===== FITS HDU INFORMATION =====")
    hdul.info()

    print("\n===== IMAGE SHAPE =====")
    for i, hdu in enumerate(hdul):
        if hdu.data is not None:
            print(i, hdu.name, hdu.data.shape)

print("\nSaved:", filename)
