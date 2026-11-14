
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
import astropy.units as u

# =====================================
# 1. SPHEREx search coordinates
# =====================================

ra = 156.09324554
dec = -41.64466099

# Convert coordinates into SkyCoord
coord = SkyCoord(ra, dec, unit="deg", frame="icrs")

# Search radius: 1 arcminute
search_radius = 1 * u.arcmin

print("Connecting to IRSA SIA...")
print("RA:", ra)
print("DEC:", dec)

# =====================================
# 2. Search SPHEREx DR1 images
# =====================================

try:
    results = Irsa.query_sia(
        pos=(coord, search_radius),
        collection="spherex_dr1"
    )

    print("\nSIA query successful!")

    # Number of images found
    print("Number of images:", len(results))

    # =================================
    # 3. Display image search results
    # =================================

    print("\nAvailable image information:")
    print("Columns:", results.colnames)

    print("\nFirst 10 images:")
    print(results[:10])

    # =================================
    # 4. Save results
    # =================================

    results.write(
        "sia_results.csv",
        format="csv",
        overwrite=True
    )

    print("\nResults saved to sia_results.csv")

    # Display image download links
    if "access_url" in results.colnames:
        print("\nFirst image URL:")
        if len(results) > 0:
            print(results["access_url"][0])

except Exception as e:
    print("\nSIA Error:")
    print(e)

print("\n===== SIA SEARCH COMPLETE =====")
