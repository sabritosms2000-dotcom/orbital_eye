
import pandas as pd

df = pd.read_csv("wise0855_corrected_results.csv")

df["observation_datetime"] = pd.to_datetime(
    df["observation_datetime"]
)

# Keep only D3 observations
d3 = df[
    df["energy_bandpassname"] == "SPHEREx-D3"
].copy()

# Exclude the first observation
d3 = d3[
    d3["observation_datetime"] >
    pd.Timestamp("2025-05-05")
]

# Select the latest D3 observation
latest = d3.sort_values(
    "observation_datetime"
).iloc[-1]

base_url = "https://irsa.ipac.caltech.edu/" + latest["uri"]

cutout_url = (
    base_url
    + "?center=133.79513,-7.24515d&size=0.1"
)

print("===== SECOND D3 OBSERVATION =====")
print("Date:", latest["observation_datetime"])
print("Plane ID:", latest["planeid"])
print("Band:", latest["energy_bandpassname"])
print("Cutout URL:", cutout_url)
