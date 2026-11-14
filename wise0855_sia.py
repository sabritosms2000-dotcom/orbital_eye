
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
import astropy.units as u

# WISE 0855 coordinates
ra = 133.79513
dec = -7.24515

target = SkyCoord(
    ra=ra,
    dec=dec,
    unit="deg",
    frame="icrs"
)

print("Searching SPHEREx SIA for WISE 0855...")

try:
    results = Irsa.query_sia(
        pos=(target, 1 * u.arcmin),
        collection="spherex_dr1"
    )

    print("\n===== WISE 0855 SIA RESULTS =====")
    print("Number of results:", len(results))
    print("Columns:", results.colnames)

    print("\nFirst 10 results:")
    print(results[:10])

    results.write(
        "wise0855_sia_results.csv",
        format="csv",
        overwrite=True
    )

    print("\nSaved: wise0855_sia_results.csv")

    print("\n===== SIA SEARCH COMPLETE =====")

except Exception as e:
    print("SIA ERROR:", e)
