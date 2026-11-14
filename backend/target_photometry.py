
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

FILES = [
    {
        "path": "../data/wise0855_first_cutout.fits",
        "x": 28.223681427148,
        "y": 28.737146168733375,
        "label": "First observation"
    },
    {
        "path": "../data/wise0855_second_cutout.fits",
        "x": 28.91226193455047,
        "y": 29.00827931613042,
        "label": "Second observation"
    }
]

APERTURE_RADIUS = 2.0
ANNULUS_INNER = 4.0
ANNULUS_OUTER = 7.0

for item in FILES:
    print("\n" + "=" * 60)
    print(item["label"])
    print("=" * 60)

    with fits.open(item["path"]) as hdul:
        image = hdul["IMAGE"].data.astype(float)
        variance = hdul["VARIANCE"].data.astype(float)
        flags = hdul["FLAGS"].data

        y_grid, x_grid = np.indices(image.shape)

        distance = np.sqrt(
            (x_grid - item["x"]) ** 2
            + (y_grid - item["y"]) ** 2
        )

        aperture = distance <= APERTURE_RADIUS

        annulus = (
            (distance >= ANNULUS_INNER)
            & (distance <= ANNULUS_OUTER)
        )

        # Use finite background pixels only
        valid_background = annulus & np.isfinite(image)

        background_values = image[valid_background]

        if len(background_values) == 0:
            print("ERROR: No valid background pixels.")
            continue

        background = np.median(background_values)

        mad = np.median(
            np.abs(background_values - background)
        )
        background_noise = 1.4826 * mad

        # Aperture measurements
        valid_aperture = aperture & np.isfinite(image)
        aperture_values = image[valid_aperture]

        pixel_count = len(aperture_values)

        net_sum = np.sum(aperture_values - background)

        # Variance contribution from aperture pixels
        valid_variance = (
            valid_aperture
            & np.isfinite(variance)
            & (variance >= 0)
        )

        variance_sum = np.sum(variance[valid_variance])

        # Include estimated local-background uncertainty
        error = np.sqrt(
            variance_sum
            + pixel_count * background_noise**2
        )

        # Approximate pixel solid angle from celestial WCS
        header = hdul["IMAGE"].header.copy()

        # Remove SIP terms to avoid applying primary distortion
        # to the alternate wavelength WCS.
        for key in list(header.keys()):
            if (
                key in ("A_ORDER", "B_ORDER", "AP_ORDER", "BP_ORDER")
                or key.startswith(("A_", "B_", "AP_", "BP_"))
            ):
                del header[key]

        wave_wcs = WCS(header, fobj=hdul, key="W")
        wavelength, bandwidth = wave_wcs.all_pix2world(
            [[item["x"], item["y"]]], 0
        )[0]

        sky_wcs = WCS(hdul["IMAGE"].header).celestial
        pixel_area_deg2 = sky_wcs.proj_plane_pixel_area().value
        pixel_area_sr = pixel_area_deg2 * (np.pi / 180.0)**2

        # Image units are MJy/sr.
        # This is aperture flux, without an aperture correction.
        flux_jy = net_sum * pixel_area_sr * 1e6
        flux_error_jy = error * pixel_area_sr * 1e6

        print(f"Target pixel: ({item['x']:.3f}, {item['y']:.3f})")
        print(f"Wavelength: {wavelength:.6f} um")
        print(f"Bandwidth: {bandwidth:.6f} um")
        print(f"Background: {background:.8f} MJy/sr")
        print(f"Background noise: {background_noise:.8f} MJy/sr")
        print(f"Aperture pixels: {pixel_count}")
        print(f"Net aperture sum: {net_sum:.8f} MJy/sr pixels")
        print(f"Uncertainty: {error:.8f} MJy/sr pixels")
        print(f"Approximate aperture flux: {flux_jy:.8e} Jy")
        print(f"Approximate flux uncertainty: {flux_error_jy:.8e} Jy")

        print("\nFlag values inside aperture:")
        values, counts = np.unique(flags[aperture], return_counts=True)

        for value, count in zip(values, counts):
            print(f"Flag {value}: {count} pixels")

        print("\nNote: Aperture correction and flag interpretation")
        print("have not yet been applied.")
