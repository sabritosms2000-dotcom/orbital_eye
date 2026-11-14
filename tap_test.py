
from astroquery.ipac.irsa import Irsa

# =====================================
# 1. SPHEREx Observation Coordinates
# =====================================

ra = 156.09324554
dec = -41.64466099

print("Connecting to IRSA TAP...")

# =====================================
# 2. ADQL Query
# =====================================

query = f"""
SELECT
    'https://irsa.ipac.caltech.edu/' || a.uri ||
    '?center={ra},{dec}d&size=0.1' AS uri,
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
AND p.energy_bandpassname = 'SPHEREx-D3'
ORDER BY p.time_bounds_lower
"""

# =====================================
# 3. Execute TAP Query
# =====================================

print("\nSearching IRSA TAP...")

try:
    results = Irsa.query_tap(query)

    # Convert results to Astropy Table
    table = results.to_table()

    print("\nTAP query successful!")

    # Number of results
    print("Number of observations:", len(table))

    # Display first 10 rows
    print("\nFirst 10 observations:")
    print(table[:10])

    # =================================
    # 4. Export Results to CSV
    # =================================

    table.write(
        "tap_results.csv",
        format="csv",
        overwrite=True
    )

    print("\nResults saved successfully!")
    print("File name: tap_results.csv")

    print("\nTotal rows:", len(table))

except Exception as e:
    print("\nAn error occurred:")
    print(e)

print("\n===== TAP ANALYSIS COMPLETE =====")
