
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import skycoord_to_pixel
import numpy as np
import matplotlib.pyplot as plt

files = [
    ("wise0855_first_cutout.fits", "May 5, 2025"),
    ("wise0855_second_cutout.fits", "May 11, 2026")
]

target = SkyCoord(
    ra=133.79513,
    dec=-7.24515,
    unit="deg",
    frame="icrs"
)

images = []
positions = []

for filename, date in files:
    with fits.open(filename) as hdul:
        image = hdul["IMAGE"].data.astype(float)
        wcs = WCS(hdul["IMAGE"].header)

        x, y = skycoord_to_pixel(target, wcs)
        x = int(np.asarray(x).item())
        y = int(np.asarray(y).item())

        images.append(image.copy())
        positions.append((x, y))

        print("\n", date)
        print("Target pixel:", x, y)
        print("Target value:", image[y, x])
        print("Image mean:", np.nanmean(image))
        print("Image median:", np.nanmedian(image))

# Use the same color limits for both images
all_values = np.concatenate([
    image[np.isfinite(image)].ravel()
    for image in images
])

vmin, vmax = np.percentile(all_values, [2, 98])

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for i in range(2):
    im = axes[i].imshow(
        images[i],
        origin="lower",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax
    )

    x, y = positions[i]

    axes[i].plot(
        x, y,
        marker="x",
        color="red",
        markersize=10,
        markeredgewidth=2
    )

    axes[i].set_title(files[i][1])
    axes[i].set_xlabel("Pixel X")
    axes[i].set_ylabel("Pixel Y")

fig.colorbar(im, ax=axes, label="MJy / sr")
fig.suptitle("WISE 0855 – Same Color Scale (SPHEREx D3)")

plt.tight_layout()
plt.savefig("wise0855_same_scale.png", dpi=200)
plt.show()

print("\nSaved: wise0855_same_scale.png")
