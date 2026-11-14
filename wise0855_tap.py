
from astroquery.ipac.irsa import Irsa

ra = 133.79513
dec = -7.24515

query = f"""
SELECT
    a.uri,
    p.planeid,
    p.time_bounds_lower,
    p.energy_bandpassname,
    p.provenance_version
FROM spherex.artifact a
JOIN spherex.plane p
ON a.planeid = p.planeid
WHERE 1 = CONTAINS(
    POINT('ICRS', {ra}, {dec}),
    p.poly
)
ORDER BY p.time_bounds_lower
"""

print("Searching SPHEREx data for WISE 0855...")

try:
    results = Irsa.query_tap(query)
    table = results.to_table()

    print("\nWISE 0855 TAP Results")
    print("Number of observations:", len(table))
    print(table[:10])

    table.write(
        "wise0855_tap_results.csv",
        format="csv",
        overwrite=True
    )

    print("\nSaved: wise0855_tap_results.csv")

except Exception as e:
    print("Error:", e)
